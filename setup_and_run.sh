#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
else
  echo "Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

echo "Setting environment variables..."
export DATABASE_URL="sqlite:///$ROOT_DIR/inventory.db"
export SECRET_KEY="change_this_secret"
export FLASK_APP="app.py"

echo "Initializing database and creating admin_user..."
python -m flask init-db

echo "Launching Flask inventory app..."
python "$ROOT_DIR/app.py"
