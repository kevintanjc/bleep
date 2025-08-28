import os
import shutil
import yaml
import pytesseract

def load_runtime_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def init_tesseract(cmd_from_config: str) -> str:
    if cmd_from_config and os.path.exists(cmd_from_config):
        pytesseract.pytesseract.tesseract_cmd = cmd_from_config
        return cmd_from_config

    tess_bin = shutil.which("tesseract")
    if tess_bin:
        pytesseract.pytesseract.tesseract_cmd = tess_bin
        return tess_bin

    for path in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                 r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return path

    raise RuntimeError("Tesseract not found. Install it or set ocr.tesseract_cmd in configs/config.yaml")
