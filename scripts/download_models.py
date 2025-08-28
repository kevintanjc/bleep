#!/usr/bin/env python3
import sys, os, shutil, urllib.request, subprocess
from pathlib import Path

ROOT = Path("backend/resources/models").resolve()
DISTIL_DIR = ROOT / "distilbert-base-uncased"
TOKENIZER_DIR = ROOT / "tokenizer"  # you already have this
YOLO_OUT = ROOT / "LP-detection.pt"

SPACY_WHL = (
    "https://github.com/explosion/spacy-models/releases/download/"
    "en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl"
)

def log(m): print(f"[models] {m}")

def ensure(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def have(path: Path, min_bytes=1024):
    return path.exists() and path.stat().st_size >= min_bytes

def pip_install(spec: str):
    cmd = [sys.executable, "-m", "pip", "install", spec]
    log(" ".join(cmd))
    subprocess.run(cmd, check=True)

def try_import(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False

def download(url: str, dest: Path):
    ensure(dest.parent)
    log(f"downloading {url} -> {dest}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    if not have(dest):
        raise RuntimeError(f"failed to download {url}")

def install_spacy():
    if try_import("en_core_web_lg"):
        log("spaCy model already installed")
        return
    pip_install(SPACY_WHL)
    if not try_import("en_core_web_lg"):
        raise RuntimeError("en_core_web_lg import failed after install")

def install_distilbert():
    # If you already exported ONNX, keep tokenizer files under models/tokenizer
    # and the ONNX at backend/resources/models/model.onnx
    # For tokenizer completeness, ensure minimal files exist
    ensure(TOKENIZER_DIR)
    needed = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
    missing = [n for n in needed if not (TOKENIZER_DIR / n).exists()]
    if missing:
        # fetch from hub if anything missing
        try:
            from huggingface_hub import snapshot_download
        except Exception:
            raise RuntimeError("huggingface_hub missing. pip install huggingface_hub")
        ensure(DISTIL_DIR)
        snapshot_download(
            repo_id="distilbert-base-uncased",
            local_dir=DISTIL_DIR,
            local_dir_use_symlinks=False,
            allow_patterns=[
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "vocab.txt",
                "config.json",
            ],
        )
        # copy tokenizer assets into your chosen folder
        for n in needed + ["vocab.txt"]:
            src = DISTIL_DIR / n
            if src.exists():
                shutil.copy2(src, TOKENIZER_DIR / n)
    log("DistilBERT tokenizer assets ready")

def install_yolo():
    # If LP-detection.pt already present, skip
    if have(YOLO_OUT, 100 * 1024):
        log(f"YOLO weights present at {YOLO_OUT}")
        return
    # If you host it elsewhere, set YOLO_SRC env var
    src = os.environ.get("YOLO_SRC", "").strip()
    if not src:
        log("YOLO_SRC not set. Skipping YOLO fetch.")
        return
    if src.startswith("http://") or src.startswith("https://"):
        download(src, YOLO_OUT)
    else:
        p = Path(src)
        if not p.exists():
            raise FileNotFoundError(f"YOLO source not found at {p}")
        ensure(YOLO_OUT.parent)
        shutil.copy2(p, YOLO_OUT)
    log(f"YOLO weights ready at {YOLO_OUT}")

def main():
    ensure(ROOT)
    install_spacy()
    install_distilbert()
    install_yolo()
    log("all models ready")

if __name__ == "__main__":
    main()
