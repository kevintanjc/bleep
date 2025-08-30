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

REM ---------- spaCy model: install once, from cached wheel ----------
set "WHEEL_URL=https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl"
set "WHEEL_NAME=en_core_web_lg-3.7.1-py3-none-any.whl"
set "WHEEL_DIR=%REPO%\.cache\wheels"
if not exist "%WHEEL_DIR%" mkdir "%WHEEL_DIR%"

REM Check if model is already installed
"%REPO%\venv\Scripts\pip" show en-core-web-lg >nul 2>&1
if errorlevel 1 (
  REM Not installed, ensure wheel is cached
  if not exist "%WHEEL_DIR%\%WHEEL_NAME%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Invoke-WebRequest -Uri '%WHEEL_URL%' -OutFile '%WHEEL_DIR%\%WHEEL_NAME%'" || (
        echo Failed to download %WHEEL_NAME%
        exit /b 1
      )
  )
  "%REPO%\venv\Scripts\pip" install "%WHEEL_DIR%\%WHEEL_NAME%" || (
    echo Failed to install %WHEEL_NAME%
    exit /b 1
  )
) else (
  echo spaCy model en-core-web-lg already installed, skipping
)

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
