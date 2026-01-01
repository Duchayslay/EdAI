import sympy as sp

def solve_system_steps(eqs):
    symbols = list(set().union(*[e.free_symbols for e in eqs]))

    steps = ["He phuong trinh:"]
    for e in eqs:
        steps.append(sp.pretty(e))

    sol = sp.solve(eqs, symbols, dict = True)

    if not sol: 
        steps.append("He vo nghiem")
        return {"steps": steps, "solution": {}}
    
    steps.append("Giai he")
    return {
        "steps": steps,
        "solution": {str(k): str(v) for k,v in sol[0].items()}

    }