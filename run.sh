#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(dirname "$0")"
REPO=$(pwd)

# ---------- Backend: venv + deps ----------
if [ ! -d "venv" ]; then
  python -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

# ---------- spaCy model: install once, from cached wheel ----------
WHEEL_URL="https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl"
WHEEL_NAME="en_core_web_lg-3.7.1-py3-none-any.whl"
WHEEL_DIR="$REPO/.cache/wheels"
mkdir -p "$WHEEL_DIR"

if ! "$REPO/venv/bin/pip" show en-core-web-lg >/dev/null 2>&1; then
  if [ ! -f "$WHEEL_DIR/$WHEEL_NAME" ]; then
    echo "Downloading $WHEEL_NAME..."
    curl -L "$WHEEL_URL" -o "$WHEEL_DIR/$WHEEL_NAME"
  fi
  echo "Installing $WHEEL_NAME..."
  "$REPO/venv/bin/pip" install "$WHEEL_DIR/$WHEEL_NAME"
else
  echo "spaCy model en-core-web-lg already installed, skipping"
fi

# Launch backend in its own terminal window
gnome-terminal --title="backend" -- bash -c "
  cd \"$REPO\" && \
  source venv/bin/activate && \
  uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload --access-log
"

# ---------- Frontend: npm install + expo ----------
pushd frontend >/dev/null
if [ ! -d "node_modules" ]; then
  npm install
else
  echo \"frontend/node_modules exists, skipping npm install\"
fi

npx expo install --fix
npm install --save-dev @types/node

# Launch frontend in its own terminal window
gnome-terminal --title="frontend" -- bash -c "
  cd \"$REPO/frontend\" && \
  npx expo start -c
"
popd >/dev/null