#!/bin/bash

echo "Starting Pi Audio Anomaly System..."
set -e

VENV_DIR="venv"

# Detect OS to handle Python and activate script paths
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PYTHON_CMD="python"
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
else
    PYTHON_CMD="python3"
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
fi

# Check if Python is installed
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: $PYTHON_CMD could not be found. Please install Python."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$ACTIVATE_SCRIPT"

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Running the application..."
python main.py
