#!/bin/bash

# GeoCongo AI - Environment Setup & Launch Script
# Optimized for Python 3.8 and QGIS Simulation Mode

set -e

PROJECT_DIR="/home/gerard/Documents/GeoKivuDoc/geocongoai-api"
VENV_DIR="$PROJECT_DIR/venv"

echo "📂 Project Directory: $PROJECT_DIR"

# 1. Diagnostic & Virtual Environment Creation
# We check for bin/activate to ensure it's a valid venv
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "🌐 Creating virtual environment (venv) with system-site-packages..."
    rm -rf "$VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
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
echo "🚀 Launching GeoCongo AI API..."
cd "$PROJECT_DIR"
# Run uvicorn as a module to ensure it uses the venv's interpreter
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
