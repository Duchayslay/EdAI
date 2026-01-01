from solver.linear import solve_linear_steps
from solver.quadratic import solve_quadratic_steps
from solver.system import solve_system_steps

def solve_with_steps(eqs):
    if len(eqs) == 1:
        expr = eqs[0].lhs - eqs[0].rhs
        deg = expr.as_poly().total_degree()

        if deg == 1:
            return solve_linear_steps(eqs[0])
        if deg == 2:
            return solve_quadratic_steps(eqs[0])
        
    if len(eqs) >= 2:
        return solve_system_steps
    
    return {
        "steps": ["Khong nhan dang duoc dang bai"],
        "solution": {}
    }
