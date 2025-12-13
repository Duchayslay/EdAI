from fastapi import FastAPI
import sympy as sp
from sympy import Eq, symbols

app = FastAPI()

@app.post("/api/solve_text")
async def solve_text(payload: dict):
    text = payload.get("text", "")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    x, y = sp.symbols("x y")
    eqs = []

    for line in lines:
        if "=" in line:
            left, right = line.split("=", 1)
            try:
                eqs.append(Eq(sp.sympify(left), sp.sympify(right)))
            except:
                pass

    if not eqs:
        return {"parsed": lines, "solution": {"message": "No equations found"}}

    try:
        sol = sp.solve(eqs, (x, y), dict=True)
        sol = sol[0] if sol else {}
    except Exception as e:
        sol = {"error": str(e)}

    return {
        "parsed": lines,
        "solution": {str(k): str(v) for k, v in sol.items()},
    }


# IMPORTANT FOR RENDER
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
