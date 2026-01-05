import re

def classify_domain(text: str) -> str:
    t = text.lower()

    if re.search(r"đạo hàm|derivative|d/dx|f'\(", t):
        return "derivative"

    if re.search(r"tích phân|integral|∫", t):
        return "integral"

    if re.search(r"phương trình|=|solve|nghiệm|x\s*=", t):
        return "equation"

    if re.search(r"tam giác|hình|góc|đường tròn|vuông", t):
        return "geometry"

    if re.search(r"xác suất|probability|thống kê", t):
        return "probability"

    return "unknown"
