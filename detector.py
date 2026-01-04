import re

def detect_type(text: str, equations: list) -> str:
    t = text.replace(" ", "").lower()

    if len(equations) >= 2:
        return "system_of_equations"

    if re.search(r"x\^2|x\*\*2", t):
        return "quadratic_equation"

    if "=" in t and "x" in t:
        return "linear_equation"

    return "word_problem"
