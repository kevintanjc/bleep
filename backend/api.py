# backend/api.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from backend.src.pipeline import process_image_bytes
import pytesseract
import yaml

def load_runtime_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)
    
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cfg = load_runtime_config("./config.yaml")
pytesseract.pytesseract.tesseract_cmd = cfg["ocr"]["tesseract_cmd"]

@app.post("/process")
async def process(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        bytes_out, meta, applied = process_image_bytes(raw, cfg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    headers = {"x-redactions": "some" if applied else "none"}
    return Response(content=bytes_out, media_type="application/octet-stream", headers=headers)
