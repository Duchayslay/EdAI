import re
from fastapi import FastAPI
import sympy as sp
from sympy import Eq

app = FastAPI()

def normalize_text(text: str):
    replacements = {
        "−": "-", "–": "-", "—": "-",
        "×": "*", "÷": "/", "＝": "=",
        " ": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def insert_multiplication(text: str):
    return re.sub(r"(\d)([a-zA-Z])", r"\1*\2", text)

def clean_ocr_lines(text: str):
    text = text.replace("X", "x").replace("Y", "y")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    merged = []
    buffer = ""

    for line in lines:
        if "=" in line:
            merged.append(buffer + line if buffer else line)
            buffer = ""
        else:
            buffer += line

    return merged

@app.post("/api/solve_text")
async def solve_text(payload: dict):
    raw = payload.get("text", "")
    text = normalize_text(raw)
    text = insert_multiplication(text)
    lines = clean_ocr_lines(text)

    x, y = sp.symbols("x y")
    eqs = []

    for line in lines:
        try:
            l, r = line.split("=", 1)
            eqs.append(Eq(sp.sympify(l), sp.sympify(r)))
        except Exception as e:
            print("Parse error:", line, e)

    if not eqs:
        return {
            "ocr_text": raw,
            "normalized": text,
            "parsed": lines,
            "solution": {"message": "No equations found"},
        }

    sol = sp.solve(eqs, (x, y), dict=True)
    sol = sol[0] if sol else {}

    return {
        "ocr_text": raw,
        "normalized": text,
        "parsed": lines,
        "solution": {str(k): str(v) for k, v in sol.items()},
    }


# IMPORTANT FOR RENDER
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
