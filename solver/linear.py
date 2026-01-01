import sympy as sp

def solve_linear_steps(eq):
    x = list(eq.free_symbols)[0] #lay bien tu do dau tien 
    lhs, rhs = eq.lhs, eq.rhs # tach ve trai, ve phai

    steps = []
    steps.append(f"Phuong trinh ban dau: {sp.pretty(eq)}")

    expr = lhs - rhs
    steps.append(f"Chuyen ve: {sp.pretty(expr)} = 0")

    sol = sp.solve(eq, x)[0]
    steps.append(f"Giai ra: {x} = {sol}")

    return {
        "steps": steps,
        "solution": {str(x): str(sol)}
    }
    