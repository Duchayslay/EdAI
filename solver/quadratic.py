import sympy as sp

def solve_quadratic_steps(eq):
    x = list(eq.free_symbols)[0]
    expr = eq.lhs - eq.rhs

    a = expr.coeff(x, 2)
    b = expr.coeff(x, 1)
    c = expr.coeff(x, 0)

    delta = b**2 - 4*a*c
    steps = [
        f"Phuong trinh: {sp.pretty(expr)} = 0",
        f"He so: a={a}, b={b}, c={c}",
        f"Tính Δ = b² - 4ac = {delta}"
    ]    
    
    sols = sp.solve(eq, x)
    if delta < 0:
        steps.append("Δ: < 0: Phuong trinh vo nghiem" )
    elif delta == 0:
        steps.append("Δ: = 0: Phuong trinh co nghiem kep{sols[0]}")
    elif delta == 0:
        steps.append("Δ > 0: Phuong trinh hai nghiem: x1={sols[0]}, x2={sols[1]}")

    return {
        "steps": steps,
        "solution": {str(x): [str(s) for s in sols]}
    }

