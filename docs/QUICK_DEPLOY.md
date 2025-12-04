# Quick Deployment Guide

## One-Line Install (Easiest!)

For a completely automated setup on your Raspberry Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/main/install.sh | bash
```

This will:
- Download docker-compose.yml and .env.example
- Generate a secure API key
- Prompt for your GitHub username
- Create the configuration

Then just:
```bash
cd ~/pi-finance
nano .env  # Review settings
docker-compose up -d
```

## Manual Install (2-File Download)

### Step 1: Download Files

```bash
mkdir -p ~/pi-finance && cd ~/pi-finance

# Download docker-compose.yml
wget -O docker-compose.yml https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/main/docker-compose.yml

# Download .env.example
wget -O .env.example https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/main/.env.example
```

### Step 2: Configure

```bash
# Copy and edit .env
cp .env.example .env
nano .env
```

Set these values in `.env`:
```env
# 1. Generate API key: openssl rand -hex 32
API_KEYS=your-generated-key-here

# 2. Set your GitHub username
GITHUB_USER=your-github-username

# 3. (Optional) Change port if 8080 is in use
API_PORT=8080
```

### Step 3: Start

```bash
docker-compose up -d
```

### Step 4: Verify

```bash
# Check logs
docker-compose logs -f

# Test API (replace with your Pi's IP)
curl http://192.168.1.100:8080/health
```

## Update

To update to the latest version:

```bash
cd ~/pi-finance
docker-compose pull
docker-compose up -d
```

## Configuration

### Required Settings

| Variable | Description | How to Get |
|----------|-------------|------------|
| `API_KEYS` | Secure API key | `openssl rand -hex 32` |
| `GITHUB_USER` | Your GitHub username | Your GitHub profile |

### Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8080 | External port (change if in use) |
| `CORS_ORIGINS` | * | Allowed origins (use `*` or specific URLs) |
| `DEBUG` | false | Debug mode (set to `true` for troubleshooting) |

## Complete `.env` Example

```env
API_KEYS=a1b2c3d4e5f6g7h8...
GITHUB_USER=yourusername
API_PORT=8080
CORS_ORIGINS=*
DEBUG=false
APP_NAME=Pi Finance API
APP_VERSION=1.0.0
```

## What Gets Pulled

The `docker-compose.yml` pulls the pre-built Docker image from:
```
ghcr.io/YOUR_USERNAME/pi-finance:latest
```

This image is automatically built by GitHub Actions whenever you push code to the `main` branch.

## Synology Reverse Proxy

Configure your Synology NAS to forward requests:

**Source:**
- Protocol: HTTPS
- Hostname: finance.yourdomain.com
- Port: 443

**Destination:**
- Protocol: HTTP
- Hostname: <raspberry-pi-ip>
- Port: 8080 (or your `API_PORT`)

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Verify .env file
cat .env
```

### Image not found

Make sure:
1. Your `GITHUB_USER` is correct in `.env`
2. GitHub Actions has built and pushed the image
3. The image is public or you're logged in: `docker login ghcr.io`

### Port already in use

Change `API_PORT` in `.env`:
```env
API_PORT=9000
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Files Downloaded

- `docker-compose.yml` - Docker Compose configuration
- `.env.example` - Environment variables template

That's it! No need to clone the entire repository.

