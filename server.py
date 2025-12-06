from fastapi import FastAPI, UploadFile, File
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import sympy as sp
import io
import pytesseract

from sympy import symbols, Eq, solve

import socket
import time
import threading
from contextlib import asynccontextmanager


def get_local_ip():
    """Return the local LAN IP address used to reach the internet.
    This is more reliable than gethostbyname(gethostname()) which may return
    loopback or hostname-mapped addresses.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # doesn't actually make a network connection; used to determine local IP
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        # fallback
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def broadcast_server_ip(stop_event: threading.Event):
    """Continuously broadcast the server IP on UDP port 50000."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set socket timeout to avoid blocking forever
        s.settimeout(1)

        while not stop_event.is_set():
            my_ip = get_local_ip()
            message = f"SERVER_IP:{my_ip}".encode()
            try:
                # Try broadcast to 255.255.255.255 (standard broadcast)
                s.sendto(message, ("255.255.255.255", 50000))
                print(f"📡 Broadcast SERVER_IP:{my_ip} to 255.255.255.255:50000")
            except Exception as e:
                print(f"⚠️  Broadcast error: {e}")
            
            # Sleep in smaller increments so we can stop quickly
            for _ in range(6):  # 3 seconds total (6 * 0.5s)
                if stop_event.is_set():
                    break
                time.sleep(0.5)
        
        s.close()
    except Exception as e:
        print(f"❌ Broadcast thread error: {e}")


def send_notification(message: str):
    """Send a one-off UDP broadcast notification on the same port used for discovery."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(message.encode(), ("255.255.255.255", 50000))
    except Exception as e:
        print(f"⚠️  send_notification error: {e}")


# Globals for broadcaster so it runs when FastAPI starts (uvicorn server:app)
stop_event = threading.Event()
broadcast_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # startup
    global broadcast_thread, stop_event
    print("🚀 Starting UDP broadcaster for server discovery...")
    if broadcast_thread is None or not broadcast_thread.is_alive():
        stop_event.clear()
        broadcast_thread = threading.Thread(target=broadcast_server_ip, args=(stop_event,), daemon=True)
        broadcast_thread.start()
        print("✓ UDP broadcaster started on port 50000")
    yield
    # shutdown
    print("🛑 Shutting down UDP broadcaster...")
    stop_event.set()
    if broadcast_thread is not None:
        broadcast_thread.join(timeout=1)
    print("✓ UDP broadcaster stopped")


app = FastAPI(lifespan=lifespan)

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

@app.post("/api/solve")
async def solve(image: UploadFile = File(...)):
    """
    Upload an image, extract text via OCR, and solve equations.
    Always returns a JSON response with error details if something fails.
    """
    try:
        # Open image
        pil_image = Image.open(image.file)
        
        # OCR
        try:
            text = pytesseract.image_to_string(pil_image, lang="eng")
        except Exception as ocr_err:
            print(f"⚠️  OCR error: {ocr_err}")
            text = f"[OCR failed: {ocr_err}]"

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        x, y = symbols("x y")
        eqs = []

        solution_result = None

        try:
            for line in lines:
                if "=" not in line:
                    # skip lines that do not look like equations
                    continue
                left, right = line.split("=", 1)
                # use sympy to parse expressions rather than eval for safety
                eqs.append(Eq(sp.sympify(left), sp.sympify(right)))

            if eqs:
                # ask sympy for solutions; prefer dict form
                sol = sp.solve(eqs, (x, y), dict=True)
                if isinstance(sol, list) and len(sol) > 0:
                    sol = sol[0]

                if isinstance(sol, dict):
                    # convert symbols to strings
                    solution_result = {"x": str(sol.get(x, sol.get(sp.Symbol('x'), ''))),
                                       "y": str(sol.get(y, sol.get(sp.Symbol('y'), '')))}
                else:
                    solution_result = {"raw": str(sol)}
            else:
                solution_result = {"message": "No equations parsed"}

        except Exception as e:
            # don't let parsing/solving crash the endpoint
            solution_result = {"error": f"Could not parse/solve equations: {e}"}

        # try to determine client IP from the underlying socket if possible
        client_ip = None
        try:
            sock = pil_image.fp.raw if hasattr(pil_image, 'fp') and hasattr(pil_image.fp, 'raw') else None
            if sock is not None and hasattr(sock, 'getpeername'):
                client_ip = sock.getpeername()[0]
        except Exception:
            client_ip = None

        # if client_ip still unknown, set to placeholder
        if not client_ip:
            client_ip = "unknown"

        # broadcast client connected notification
        try:
            send_notification(f"CLIENT_CONNECTED:{client_ip}")
            print(f"✓ Client connected: {client_ip}")
        except Exception as e:
            print(f"⚠️  Failed to send client notification: {e}")

        return {
            "ocr_text": text,
            "parsed": lines,
            "solution": solution_result,
            "client_ip": client_ip,
        }
    
    except Exception as e:
        # Catch-all for any unexpected error
        print(f"❌ /api/solve error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ocr_text": None,
            "parsed": [],
            "solution": {"error": f"Server error: {e}"},
            "client_ip": "unknown",
        }


if __name__ == "__main__":
    # run uvicorn directly so `python3 server.py` starts the HTTP server on 0.0.0.0
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

print("DEBUG: before loading model")
processor = ...
print("DEBUG: after loading model")
