import re
import os
from fastapi import FastAPI
import sympy as sp
from sympy import Eq
from classifier import classify_domain
from detector import detect_type
from supabase import create_client
from solver.step_solver import solve_with_steps

# =====================
# INIT
# =====================
app = FastAPI()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# UTILS
# =====================
def normalize_text(text: str) -> str:
    replacements = {
        "−": "-",
        "–": "-",
        "—": "-",
        "×": "*",
        "÷": "/",
        "＝": "=",
        "²": "**2",
        "³": "**3",
        " ": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def insert_multiplication(text: str):
    return re.sub(r"(\d)([a-zA-Z])", r"\1*\2", text)

def clean_ocr_lines(text: str):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    cleaned = []
    buffer = ""

    for line in lines:
        if re.fullmatch(r"\d+", line) and buffer:
            buffer += "=" + line
            cleaned.append(buffer)
            buffer = ""
        elif "=" in line:
            if buffer:
                cleaned.append(buffer)
                buffer = ""
            cleaned.append(line)
        else:
            buffer = line

    if buffer:
        cleaned.append(buffer)
    return cleaned

@app.post("/api/solve_text")
async def solve_text(payload: dict):
    raw = payload.get("text", "").strip()
    if not raw:
        return {"error": "Empty text"}

    text = insert_multiplication(normalize_text(raw))
    lines = clean_ocr_lines(text)

    eqs = []
    for line in lines:
        try:
            l, r = line.split("=", 1)
            eqs.append(Eq(sp.sympify(l), sp.sympify(r)))
        except:
            pass

    domain = classify_domain(raw)
    problem_type = detect_type(text, eqs)

    step_result = solve_with_steps(eqs)

    result = {
        "domain": domain,
        "type": problem_type,
        "ocr_text": raw,
        "normalized": text,
        "parsed": lines,
        "steps": step_result["steps"],
        "solution": step_result["solution"],
    }

    supabase.table("solve_history").insert({
        "user_id": payload.get("user_id"),
        "raw_text": raw,
        "normalized_text": text,
        "parsed_lines": lines,
        "problem_type": problem_type,
        "solution": step_result["solution"],
    }).execute()

    return result

@app.get("/api/history")
async def get_history():
    res = supabase.table("solve_history") \
        .select("*") \
        .order("created_at", desc=True) \
        .limit(50) \
        .execute()
    return res.data
