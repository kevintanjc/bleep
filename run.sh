#!/bin/bash
set -e
cd "$(dirname "$0")"

# Create virtual environment if not exists
if [ ! -d "bleep" ]; then
    echo "Creating virtual environment 'bleep'..."
    python3 -m venv bleep
fi

# Activate venv
echo "Activating virtual environment..."
source bleep/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "All set. Run your project with:"
echo "    source bleep/bin/activate && python bleep/backend/main.py"
