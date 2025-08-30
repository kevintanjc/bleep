from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from main import load_runtime_config
from PIL import Image, UnidentifiedImageError
import io
import numpy as np
import yaml

from .src.detection import process_image_np  # must accept and return RGB ndarrays

app = FastAPI()

# CORS, set real origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 20 * 1024 * 1024  # 20 MB

CFG = load_runtime_config("config.yaml")

def ensure_image_ct(content_type: str) -> None:
    if content_type not in ALLOWED:
        raise HTTPException(415, f"Unsupported Content-Type {content_type}")

@app.post("/process")
async def process(file: UploadFile = File(...)):
    ensure_image_ct(file.content_type)

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file")
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"File too large, max {MAX_BYTES} bytes")

    # Decode once, verify, then reopen and convert to RGB
    try:
        Image.open(io.BytesIO(raw)).verify()
        pil_in = Image.open(io.BytesIO(raw)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(400, "Uploaded data is not a valid image")
    except Exception as e:
        raise HTTPException(400, f"Image parse error: {e}")

    # PIL Image -> NumPy RGB
    img_rgb = np.array(pil_in)
    if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        raise HTTPException(400, f"Expected RGB image, got shape {img_rgb.shape}")

    # Process on ndarray, then encode to JPEG
    try:
        redacted_rgb, meta, applied = process_image_np(img_rgb, CFG)
    except Exception as e:
        raise HTTPException(500, f"processing error: {type(e).__name__}: {e}")

    if redacted_rgb.ndim != 3 or redacted_rgb.shape[2] != 3:
        raise HTTPException(500, f"Processor returned invalid shape {redacted_rgb.shape}")

    buf = io.BytesIO()
    Image.fromarray(redacted_rgb, mode="RGB").save(buf, format="JPEG", quality=90)
    jpeg_bytes = buf.getvalue()

    if not jpeg_bytes:
        raise HTTPException(500, "processing returned empty bytes")

    print(
        f"[process] ct_in={file.content_type} size_in={len(raw)}B "
        f"out_shape={redacted_rgb.shape} size_out={len(jpeg_bytes)}B "
        f"applied={applied} counts={meta.get('counts')}"
    )

    headers = {
        "Content-Disposition": 'inline; filename="result.jpg"',
        "X-Redactions": "some" if applied else "none",
    }
    return Response(content=jpeg_bytes, media_type="image/jpeg", headers=headers)
