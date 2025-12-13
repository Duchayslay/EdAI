import re
import sympy as sp
from sympy import Eq

def clean_ocr_lines(text: str):
    text = text.replace("X", "x").replace("Y", "y")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    cleaned = []
    buffer = ""

    for line in lines:
        # bỏ dòng chỉ có số đơn lẻ
        if re.fullmatch(r"\d+", line):
            buffer += " = " + line
            cleaned.append(buffer)
            buffer = ""
            continue

        if "=" in line:
            if buffer:
                cleaned.append(buffer)
                buffer = ""
            cleaned.append(line)
        else:
            buffer = line

    return cleaned


@app.post("/api/solve_text")
async def solve_text(payload: dict):
    text = payload.get("text", "")
    lines = clean_ocr_lines(text)

    x, y = sp.symbols("x y")
    eqs = []

    for line in lines:
        try:
            left, right = line.split("=", 1)
            eqs.append(Eq(sp.sympify(left), sp.sympify(right)))
        except:
            pass

    if not eqs:
        return {
            "ocr_text": text,
            "parsed": lines,
            "solution": {"message": "No equations found"}
        }

    sol = sp.solve(eqs, (x, y), dict=True)
    sol = sol[0] if sol else {}

    return {
        "ocr_text": text,
        "parsed": lines,
        "solution": {str(k): str(v) for k, v in sol.items()},
    }



# IMPORTANT FOR RENDER
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
