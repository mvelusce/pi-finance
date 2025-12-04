#!/bin/bash

# Quick Start Script for Pi Finance API
# This script helps you get started quickly with local development

set -e  # Exit on error

echo "================================================"
echo "  Pi Finance API - Quick Start Setup"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    
    # Generate API key
    if command -v openssl &> /dev/null; then
        API_KEY=$(openssl rand -hex 32)
        # Replace the placeholder in .env
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/your-secret-api-key-here,another-key-if-needed/$API_KEY/" .env
        else
            # Linux
            sed -i "s/your-secret-api-key-here,another-key-if-needed/$API_KEY/" .env
        fi
        echo "✓ .env file created with generated API key"
        echo ""
        echo "🔑 Your API Key: $API_KEY"
        echo "   (This is also saved in .env file)"
    else
        echo "✓ .env file created"
        echo "⚠️  Please manually generate an API key and update .env"
        echo "   Run: openssl rand -hex 32"
    fi
else
    echo "✓ .env file already exists"
fi

echo ""
echo "================================================"
echo "  Setup Complete! 🎉"
echo "================================================"
echo ""
echo "To start the API:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the API: uvicorn app.main:app --reload"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
echo "The API will be available at:"
echo "  • API: http://localhost:8000"
echo "  • Docs: http://localhost:8000/docs"
echo ""
echo "Your API key is in the .env file"
echo "================================================"

