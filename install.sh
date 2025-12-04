#!/bin/bash
# Quick setup script for Pi Finance API on Raspberry Pi
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/master/install.sh | bash

set -e

echo "================================================"
echo "  Pi Finance API - Quick Install"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "Install Docker with: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "✓ Docker found"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available."
    echo "Install Docker Compose plugin with: sudo apt-get install docker-compose-plugin"
    exit 1
fi

echo "✓ Docker Compose found"

# Create directory
INSTALL_DIR="${INSTALL_DIR:-$HOME/pi-finance}"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo ""
echo "📥 Downloading configuration files..."

# Download docker-compose.yml
if ! curl -fsSL -o docker-compose.yml https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/master/docker-compose.yml; then
    echo "❌ Failed to download docker-compose.yml"
    exit 1
fi

# Download .env.example
if ! curl -fsSL -o .env.example https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/master/.env.example; then
    echo "❌ Failed to download .env.example"
    exit 1
fi

echo "✓ Files downloaded to $INSTALL_DIR"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    
    # Generate API key if openssl is available
    if command -v openssl &> /dev/null; then
        API_KEY=$(openssl rand -hex 32)
        sed -i "s/your-secret-api-key-here,another-key-if-needed/$API_KEY/" .env 2>/dev/null || \
        sed -i'' -e "s/your-secret-api-key-here,another-key-if-needed/$API_KEY/" .env
        echo "✓ Generated secure API key"
    else
        echo "⚠️  Please generate an API key manually and update .env"
        echo "   Run: openssl rand -hex 32"
    fi
    
    # Prompt for GitHub username
    echo ""
    echo "Please enter your GitHub username (for pulling the Docker image):"
    read -r GITHUB_USER
    if [ -n "$GITHUB_USER" ]; then
        echo "GITHUB_USER=$GITHUB_USER" >> .env
        echo "✓ GitHub username set to: $GITHUB_USER"
    fi
else
    echo "✓ .env file already exists"
fi

echo ""
echo "================================================"
echo "  Installation Complete! 🎉"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Review your configuration:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2. Make sure to set:"
echo "   - API_KEYS (your secure API key)"
echo "   - GITHUB_USER (your GitHub username)"
echo "   - API_PORT (change if 8080 is in use)"
echo ""
echo "3. Start the service:"
echo "   cd $INSTALL_DIR"
echo "   docker-compose up -d"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Access your API:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "================================================"

