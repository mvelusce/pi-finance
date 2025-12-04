#!/bin/bash
# Startup script for Pi Finance API
# This ensures the correct Python is used, avoiding pyenv conflicts

cd "$(dirname "$0")"

# Load port from .env file if it exists, otherwise default to 8080
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep API_PORT | xargs)
fi

PORT=${API_PORT:-8080}

echo "Starting Pi Finance API on port $PORT..."

# Explicitly use the venv's Python
./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
