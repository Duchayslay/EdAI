import re
import os
from fastapi import FastAPI
import sympy as sp
from sympy import Eq
from classifier import classify_domain
from detector import detect_type
from supabase import create_client
from solver.step_solver import solve_with_steps
import traceback

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

# =====================
# POST /solve_text
# =====================
@app.post("/api/solve_text")
async def solve_text(payload: dict):
    raw = payload.get("text", "").strip()
    if not raw:
        return {"error": "Empty text"}

    try:
        text = insert_multiplication(normalize_text(raw))
        lines = clean_ocr_lines(text)

        eqs = []
        parse_errors = []
        for line in lines:
            try:
                l, r = line.split("=", 1)
                eqs.append(Eq(sp.sympify(l), sp.sympify(r)))
            except Exception as e:
                parse_errors.append({"line": line, "error": str(e)})
                print("Parse error:", line, e)

        if not eqs:
            return {
                "error": "Cannot parse",
                "ocr_text": raw,
                "normalized": text,
                "parsed": lines,
                "parse_errors": parse_errors
            }

        step_result = solve_with_steps(eqs)
        problem_type = detect_type(text, eqs)
        domain = classify_domain(text)

        result = {
            "domain": domain,
            "type": problem_type,
            "ocr_text": raw,
            "normalized": text,
            "parsed": lines,
            "steps": step_result.get("steps", []),
            "solution": step_result.get("solution", {}),
            "parse_errors": parse_errors
        }

        # Lưu vào supabase, nhưng không crash nếu lỗi
        try:
            supabase.table("solve_history").insert({
                "user_id": payload.get("user_id"),
                "raw_text": raw,
                "normalized_text": text,
                "parsed_lines": lines,
                "problem_type": problem_type,
                "solution": step_result.get("solution", {}),
                "parse_errors": parse_errors
            }).execute()
        except Exception as e:
            print("Supabase insert failed:", e)

        return result

    except Exception as e:
        traceback.print_exc()
        return {"error": "Internal server error", "message": str(e)}

# =====================
# GET /history
# =====================
@app.get("/api/history")
async def get_history():
    try:
        res = supabase.table("solve_history") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        return res.data
    except Exception as e:
        traceback.print_exc()
        return {"error": "Cannot fetch history", "message": str(e)}
import subprocess

@app.get("/api/version")
async def get_version():
    try:
        # Lấy commit hash hiện tại
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=os.getcwd())
        return {"commit": commit.decode().strip()}
    except Exception as e:
        return {"error": str(e)}
