@echo off
setlocal enabledelayedexpansion

REM Always run from repo root
cd /d "%~dp0"
set "REPO=%CD%"

REM ---------- Backend: venv + deps ----------
if not exist "%REPO%\venv" (
  py -3 -m venv "%REPO%\venv"
)
call "%REPO%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
python -m pip install -r "%REPO%\requirements.txt"

REM Launch backend in its own terminal
start "backend" cmd /k ""%REPO%\venv\Scripts\python.exe" -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload --access-log"

REM ---------- Frontend: deps ----------
pushd "%REPO%\frontend"
if not exist node_modules (
  call npm install
) else (
  echo frontend\node_modules exists, skipping npm install
)

call npx expo install --fix
call npm install --save-dev @types/node

REM Launch Expo in its own terminal so the QR code is visible
start "frontend" cmd /k "cd /d "%REPO%\frontend" && npx expo start -c"
popd

endlocal
