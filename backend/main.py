from backend.src.detection import run_pipeline
import pytesseract
import yaml

def load_runtime_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)
    

def main():
    cfg = load_runtime_config("config.yaml")
    pytesseract.pytesseract.tesseract_cmd = cfg["ocr"]["tesseract_cmd"]

    reports = run_pipeline(load_runtime_config("config.yaml"))
    for r in reports:
        print(f"Report: {r}")

if __name__ == "__main__":
    main()
