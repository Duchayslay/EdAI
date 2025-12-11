from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import sympy as sp
from sympy import symbols, Eq
import io
import torch
from transformers import VisionEncoderDecoderModel, TrOCRProcessor

# ============================
# Load model (nhẹ, phù hợp Render)
# ============================
device = "cpu"

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
model.to(device)

# ============================
# FastAPI
# ============================
app = FastAPI()

# CORS cho phép Flutter gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# API Solve
# ============================
@app.post("/api/solve")
async def solve(image: UploadFile = File(...)):
    try:
        # đọc ảnh từ upload
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # ======================
        # 1) OCR bằng TrOCR
        # ======================
        pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values.to(device)

        with torch.no_grad():
            generated_ids = model.generate(pixel_values)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # ======================
        # 2) Tách dòng hợp lệ
        # ======================
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # ======================
        # 3) Giải phương trình bằng SymPy
        # ======================
        x, y = symbols("x y")
        eqs = []

        for line in lines:
            if "=" in line:
                left, right = line.split("=", 1)
                try:
                    eqs.append(Eq(sp.sympify(left), sp.sympify(right)))
                except Exception:
                    pass

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
            "solution": {str(k): str(v) for k, v in solution.items()}
        }

    except Exception as e:
        return {
            "ocr_text": "",
            "parsed": [],
            "solution": {"error": str(e)}
        }
