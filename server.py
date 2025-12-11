from fastapi import FastAPI, UploadFile, File
import requests
import sympy as sp
from sympy import Eq, symbols

API_KEY = "helloworld"  # Free key

app = FastAPI()

@app.post("/api/solve")
async def solve(image: UploadFile = File(...)):
    try:
        # Gửi ảnh lên OCR.Space
        ocr_result = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": (image.filename, image.file, image.content_type)},
            data={"apikey": API_KEY, "language": "eng"}
        ).json()

        text = ocr_result["ParsedResults"][0]["ParsedText"]

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        x, y = symbols("x y")
        eqs = []
        for line in lines:
            if "=" in line:
                left, right = line.split("=", 1)
                eqs.append(Eq(sp.sympify(left), sp.sympify(right)))

        solution = {}
        if eqs:
            sol = sp.solve(eqs, (x, y), dict=True)
            solution = sol[0] if sol else {}
        else:
            solution = {"message": "No equations found"}

        return {
            "ocr_text": text,
            "parsed": lines,
            "solution": {str(k): str(v) for k, v in solution.items()},
        }

    except Exception as e:
        return {"error": str(e)}
