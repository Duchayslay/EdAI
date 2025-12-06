from fastapi import FastAPI, UploadFile, File
from PIL import Image
import pytesseract
import sympy as sp
from sympy import symbols, Eq
from contextlib import asynccontextmanager
import socket
import threading
import time


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


def broadcast_server_ip(stop_event: threading.Event):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(1)

        while not stop_event.is_set():
            ip = get_local_ip()
            msg = f"SERVER_IP:{ip}".encode()

            try:
                s.sendto(msg, ("255.255.255.255", 50000))
            except:
                pass

            for _ in range(6):
                if stop_event.is_set():
                    break
                time.sleep(0.5)

        s.close()

    except:
        pass


stop_event = threading.Event()
broadcast_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcast_thread, stop_event
    stop_event.clear()

    broadcast_thread = threading.Thread(
        target=broadcast_server_ip, args=(stop_event,), daemon=True
    )
    broadcast_thread.start()
    yield

    stop_event.set()
    if broadcast_thread is not None:
        broadcast_thread.join(timeout=1)


app = FastAPI(lifespan=lifespan)


@app.post("/api/solve")
async def solve(image: UploadFile = File(...)):
    try:
        pil_image = Image.open(image.file)

        # OCR bằng Tesseract
        text = pytesseract.image_to_string(pil_image, lang="eng")

        # Tách dòng hợp lệ
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        x, y = symbols("x y")
        eqs = []
        for line in lines:
            if "=" in line:
                left, right = line.split("=", 1)
                eqs.append(Eq(sp.sympify(left), sp.sympify(right)))

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
            "solution": {str(k): str(v) for k, v in solution.items()},
        }

    except Exception as e:
        return {
            "ocr_text": "",
            "parsed": [],
            "solution": {"error": str(e)}
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
