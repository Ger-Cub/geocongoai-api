#!/bin/bash

# GeoCongo AI - Environment Setup & Launch Script
# Optimized for Python 3.8 and QGIS Simulation Mode

set -e

PROJECT_DIR="/home/gerard/Documents/GeoKivuDoc/geocongoai-api"
VENV_DIR="$PROJECT_DIR/venv"

echo "📂 Project Directory: $PROJECT_DIR"

# 1. Diagnostic & Virtual Environment Creation
# TerraTorch requires Python >= 3.10
if command -v pyenv >/dev/null 2>&1; then
    # Use 3.10.13 from pyenv if available
    if pyenv versions | grep -q "3.10.13"; then
        export PYENV_VERSION=3.10.13
    fi
fi

PYTHON_EXE=$(command -v python3.10 || command -v python3.11 || command -v python3.12 || echo "python3")

# Check current venv version
if [ -f "$VENV_DIR/bin/python" ]; then
    VENV_VERSION=$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    # Use python for proper version comparison
    IS_OLD=$($PYTHON_EXE -c "import sys; print(1 if [int(x) for x in '$VENV_VERSION'.split('.')] < [3, 10] else 0)")
    if [ "$IS_OLD" -eq 1 ]; then
        echo "⚠️  Existing venv is Python $VENV_VERSION. Recreating with Python 3.10+ for TerraTorch support..."
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "🌐 Creating virtual environment (venv) with $PYTHON_EXE..."
    rm -rf "$VENV_DIR"
    $PYTHON_EXE -m venv "$VENV_DIR"
else
    echo "✅ Virtual environment found and valid."
fi

# 2. Activation
echo "🔌 Activating environment..."
source "$VENV_DIR/bin/activate"

# 3. Dependency Installation
echo "📦 Installing/Updating dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# 4. Launch
echo "🚀 Launching Gundua Engine..."
cd "$PROJECT_DIR"
# Run uvicorn as a module to ensure it uses the venv's interpreter
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
