from fastapi import FastAPI, UploadFile, File
from PIL import Image
import pytesseract
import sympy as sp
from sympy import symbols, Eq
from contextlib import asynccontextmanager


app = FastAPI()


@app.post("/api/solve")
async def solve(image: UploadFile = File(...)):
    try:
        pil_image = Image.open(image.file)

        # OCR bằng Tesseract
        text = pytesseract.image_to_string(pil_image, lang="eng")

        # Tách dòng hợp lệ
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        x, y = symbols("x y")
        eqs = []
        for line in lines:
            if "=" in line:
                left, right = line.split("=", 1)
                eqs.append(Eq(sp.sympify(left), sp.sympify(right)))

        solution = {}
        if eqs:
            try:
                sol = sp.solve(eqs, (x, y), dict=True)
                solution = sol[0] if isinstance(sol, list) and sol else {}
            except Exception as e:
                solution = {"error": f"Cannot solve: {e}"}
        else:
            solution = {"message": "No equations found"}

        return {
            "ocr_text": text,
            "parsed": lines,
            "solution": {str(k): str(v) for k, v in solution.items()},
        }

    except Exception as e:
        return {
            "ocr_text": "",
            "parsed": [],
            "solution": {"error": str(e)}
        }

