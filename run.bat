@echo off
setlocal enabledelayedexpansion

REM repo root
cd /d %~dp0

REM venv
if not exist .venv (
    py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

py -m pip install --upgrade pip
py -m pip install -r requirements.txt

REM optional, set YOLO_SRC to a URL or local path
REM set YOLO_SRC=https://huggingface.co/MKgoud/License-Plate-Recognizer/resolve/main/LP-detection.pt
py scripts\download_models.py

if not exist backend\results mkdir backend\results

uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
