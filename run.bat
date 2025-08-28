@echo off
SETLOCAL
cd /d "%~dp0"

REM Check if venv exists
IF NOT EXIST bleep (
    echo Creating virtual environment "bleep"...
    python -m venv bleep
)

REM Activate venv
echo Activating virtual environment...
CALL bleep\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt

ENDLOCAL
