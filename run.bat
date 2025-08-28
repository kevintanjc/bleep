@echo off
SETLOCAL
cd /d "%~dp0"

REM Check if venv exists
IF NOT EXIST venv (
    echo Creating virtual environment "venv"...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
CALL venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt

ENDLOCAL
