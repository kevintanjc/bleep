#!/usr/bin/env bash
set -e

# repo root
cd "$(dirname "$0")"

# venv
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate

python -m pip install --upgrade pip

# prefer pyproject if present, then requirements.txt
if [ -f "pyproject.toml" ]; then
  pip install -e .
else
  pip install -r requirements.txt
fi

# fetch models
export YOLO_SRC=https://huggingface.co/MKgoud/License-Plate-Recognizer/resolve/main/LP-detection.pt
python scripts/download_models.py

# sanity folders
mkdir -p backend/results

# launch app
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
