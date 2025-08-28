from pathlib import Path
from backend.src.pipeline import run_pipeline
from backend.src.load_config import load_runtime_config, init_tesseract

def main():
    cfg = load_runtime_config("./config.yaml")
    if cfg["ocr"].get("tesseract_cmd", ""):
        init_tesseract(cfg["ocr"]["tesseract_cmd"])
    else:
        init_tesseract("")

    reports = run_pipeline(cfg)
    for r in reports:
        print(f"Report: {r}")

if __name__ == "__main__":
    main()
