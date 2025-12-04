# Deployment Guide - Pi Finance API

This guide walks you through deploying the Pi Finance API on your Raspberry Pi with HTTPS support via your Synology reverse proxy.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Deployment Options](#deployment-options)
4. [Reverse Proxy Configuration](#reverse-proxy-configuration)
5. [Testing](#testing)
6. [Maintenance](#maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Your Raspberry Pi

- **Operating System**: Raspberry Pi OS (formerly Raspbian) or similar
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later

Install Docker and Docker Compose if not already installed:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid using sudo)
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Reboot or logout/login for group changes to take effect
sudo reboot
```

### On Your Development Machine

- Git
- Text editor
- SSH client
- (Optional) Docker for local testing

### Network Requirements

- Raspberry Pi accessible from your Synology NAS
- Synology NAS configured with reverse proxy capability
- Domain name pointing to your Synology NAS
- SSL certificate configured on Synology

---

## Initial Setup

### 1. Generate API Key

On your development machine or Pi, generate a secure API key:

```bash
openssl rand -hex 32
```

Save this key securely - you'll need it for configuration and Google Sheets.

Example output:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### 2. Clone Repository on Raspberry Pi

SSH into your Raspberry Pi:

```bash
ssh pi@raspberrypi.local
# Or use the IP: ssh pi@192.168.1.100
```

Clone the repository:

```bash
cd ~
git clone https://github.com/your-username/pi-finance.git
cd pi-finance
```

### 3. Configure Environment

Create the `.env` file from the example:

```bash
cp .env.example .env
nano .env
```

Update the configuration:

```env
# Replace with your generated API key
API_KEYS=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

# For Google Sheets, you can restrict to Google domains:
CORS_ORIGINS=https://sheets.google.com,https://script.google.com,https://docs.google.com

# Or allow all (less secure but simpler):
# CORS_ORIGINS=*

# Keep debug off in production
DEBUG=false
```

Save and exit (Ctrl+X, Y, Enter in nano).

---

## Deployment Options

### Option A: Using Docker Compose (Recommended)

This is the simplest method for ongoing management.

**1. Build and Start**

```bash
cd ~/pi-finance
docker-compose up -d
```

The `-d` flag runs it in detached mode (background).

**2. Verify it's running**

```bash
docker-compose ps
```

You should see:

```
NAME                COMMAND                  SERVICE   STATUS    PORTS
pi-finance-api      "uvicorn app.main:ap…"   api       Up        0.0.0.0:8000->8000/tcp
```

**3. Check logs**

```bash
docker-compose logs -f
```

Press Ctrl+C to exit logs.

**4. Test locally**

```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","timestamp":"2025-12-03T..."}
```

Test with authentication:
```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/quote/AAPL
```

### Option B: Using Pre-built Docker Image

If you've set up GitHub Actions, pull the pre-built image:

**1. Login to GitHub Container Registry**

```bash
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u your-username --password-stdin
```

**2. Pull and run**

```bash
docker pull ghcr.io/your-username/pi-finance:master

docker run -d \
  --name pi-finance-api \
  -p 8000:8000 \
  -e API_KEYS="your-api-key-here" \
  -e CORS_ORIGINS="*" \
  -e DEBUG="false" \
  --restart unless-stopped \
  ghcr.io/your-username/pi-finance:master
```

**3. Verify**

```bash
docker ps
docker logs pi-finance-api
```

### Option C: Local Development Build

For development and testing:

**1. Install Python dependencies**

```bash
cd ~/pi-finance
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Run directly**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Reverse Proxy Configuration

### Synology Reverse Proxy Setup

**1. Access Synology Control Panel**

- Log in to your Synology DSM
- Go to **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**

**2. Create New Reverse Proxy Rule**

Click **Create** and configure:

**General Tab:**
- **Description**: Pi Finance API
- **Source:**
  - Protocol: `HTTPS`
  - Hostname: `finance.yourdomain.com` (or subdomain of your choice)
  - Port: `443`
  - Enable HSTS: ✓ (checked)
  - Enable HTTP/2: ✓ (checked - optional but recommended)

- **Destination:**
  - Protocol: `HTTP`
  - Hostname: `192.168.1.100` (your Raspberry Pi's IP)
  - Port: `8000`

**Custom Header Tab (Optional but Recommended):**

Add these headers for better security:

Click **Create** → **WebSocket**
- Leave WebSocket settings as default (not needed for this API)

**3. Save Configuration**

Click **OK** to save.

**4. DNS Configuration**

Ensure your domain/subdomain points to your public IP:

- If using dynamic DNS: Configure through Synology or external provider
- If using your own domain: Add an A record pointing to your public IP

**5. Port Forwarding (If needed)**

On your router, forward port 443 to your Synology NAS if external access is needed.

### Testing Reverse Proxy

**1. Test from within your network:**

```bash
curl https://finance.yourdomain.com/health
```

**2. Test from external network:**

Use your phone's data connection or external server:
```bash
curl https://finance.yourdomain.com/health
```

**3. Test with authentication:**

```bash
curl -H "X-API-Key: your-api-key-here" https://finance.yourdomain.com/quote/AAPL
```

---

## Testing

### API Endpoint Testing

**1. Health Check (No Auth)**
```bash
curl https://finance.yourdomain.com/health
```

**2. Root Endpoint (No Auth)**
```bash
curl https://finance.yourdomain.com/
```

**3. Get Stock Quote**
```bash
curl -H "X-API-Key: your-api-key" https://finance.yourdomain.com/quote/AAPL
```

**4. Get Multiple Quotes**
```bash
curl -H "X-API-Key: your-api-key" "https://finance.yourdomain.com/quotes?symbols=AAPL,MSFT,GOOGL"
```

**5. Get Company Info**
```bash
curl -H "X-API-Key: your-api-key" https://finance.yourdomain.com/info/AAPL
```

**6. Get Historical Data**
```bash
curl -X POST https://finance.yourdomain.com/history \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1mo", "interval": "1d"}'
```

### Google Sheets Integration Testing

**1. Set up Apps Script**

- Open a Google Sheet
- Go to **Extensions** → **Apps Script**
- Copy the code from `google-sheets-integration.js`
- Update `API_URL` and `API_KEY`
- Save the project

**2. Test Connection**

In Apps Script editor:
- Select function: `testAPIConnection`
- Click **Run**
- Check **Execution log** for results

**3. Use in Sheet**

In a cell, try:
```
=APISTATUS()
```

Should show: `Connected ✓`

Then try:
```
=STOCKPRICE("AAPL")
```

---

## Maintenance

### Updating the Application

**Method 1: Using Docker Compose (Recommended)**

```bash
cd ~/pi-finance
git pull origin master
docker-compose down
docker-compose up -d --build
```

**Method 2: Using Pre-built Image**

```bash
docker pull ghcr.io/your-username/pi-finance:master
docker stop pi-finance-api
docker rm pi-finance-api
docker run -d \
  --name pi-finance-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/your-username/pi-finance:master
```

### Viewing Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f pi-finance-api

# Last 100 lines
docker-compose logs --tail 100
```

### Restarting the Service

```bash
# Docker Compose
docker-compose restart

# Docker
docker restart pi-finance-api
```

### Stopping the Service

```bash
# Docker Compose
docker-compose down

# Docker
docker stop pi-finance-api
```

### Backup Configuration

```bash
# Backup your .env file
cp ~/.pi-finance/.env ~/.pi-finance/.env.backup

# Or create a backup script
tar -czf pi-finance-backup-$(date +%Y%m%d).tar.gz ~/pi-finance/.env
```

### System Resources Monitoring

```bash
# Check CPU/Memory usage
docker stats pi-finance-api

# Check disk space
df -h

# Check container health
docker inspect --format='{{.State.Health.Status}}' pi-finance-api
```

### Automatic Updates (Optional)

Create a cron job for automatic updates:

```bash
crontab -e
```

Add this line to update weekly:
```cron
0 3 * * 0 cd /home/pi/pi-finance && docker-compose pull && docker-compose up -d
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs
```

**Common issues:**

1. **Port already in use:**
   ```bash
   # Check what's using port 8000
   sudo lsof -i :8000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Permission issues:**
   ```bash
   # Ensure .env file is readable
   chmod 644 .env
   
   # Check Docker group membership
   groups $USER
   ```

3. **Out of disk space:**
   ```bash
   df -h
   docker system prune -a  # Remove unused images
   ```

### API Returns 401 Unauthorized

**Issue:** `X-API-Key` header missing or incorrect

**Solution:**
1. Verify your API key in `.env` matches your request
2. Check the header name is exactly `X-API-Key` (case-sensitive)
3. Test with curl:
   ```bash
   curl -v -H "X-API-Key: your-key" https://finance.yourdomain.com/quote/AAPL
   ```

### API Returns 403 Forbidden

**Issue:** API key is provided but invalid

**Solution:**
1. Regenerate API key: `openssl rand -hex 32`
2. Update `.env` file
3. Restart container: `docker-compose restart`

### Cannot Access via HTTPS

**Issue:** Reverse proxy not working

**Checklist:**
1. ✓ Synology reverse proxy rule created
2. ✓ DNS record pointing to your public IP
3. ✓ Port 443 forwarded to Synology (if accessing externally)
4. ✓ SSL certificate valid on Synology
5. ✓ Pi's IP address correct in reverse proxy destination
6. ✓ Container running on Pi (check with `docker ps`)

**Test:**
```bash
# From Pi - test local API
curl http://localhost:8000/health

# From another device on network - test reverse proxy
curl https://finance.yourdomain.com/health
```

### Google Sheets Functions Not Working

**Issue:** Functions return errors

**Solutions:**

1. **Test API directly:**
   ```bash
   curl -H "X-API-Key: your-key" https://finance.yourdomain.com/quote/AAPL
   ```

2. **Check Apps Script logs:**
   - Apps Script editor → **Executions**
   - Look for error messages

3. **Verify CORS settings:**
   ```env
   # In .env file
   CORS_ORIGINS=https://sheets.google.com,https://script.google.com
   ```

4. **Re-authorize Apps Script:**
   - Apps Script editor → Run `testAPIConnection`
   - Grant permissions when prompted

5. **Check API_KEY in script:**
   - Ensure it matches your `.env` configuration

### Data is Stale or Incorrect

**Issue:** Yahoo Finance API limitations

**Solutions:**

1. **Check if symbol is valid:**
   ```bash
   curl -H "X-API-Key: your-key" https://finance.yourdomain.com/quote/INVALID
   ```

2. **Try different symbol:**
   Market data availability varies

3. **Check yfinance status:**
   - GitHub: https://github.com/ranaroussi/yfinance/issues
   - Yahoo Finance may have temporary outages

4. **Force refresh in Google Sheets:**
   - Edit and re-enter formula
   - Or change cell to force recalculation

### High Memory Usage

**Issue:** Container using too much memory

**Solutions:**

1. **Check current usage:**
   ```bash
   docker stats pi-finance-api
   ```

2. **Limit memory in docker-compose.yml:**
   ```yaml
   services:
     api:
       # ... existing config ...
       deploy:
         resources:
           limits:
             memory: 512M
   ```

3. **Restart container:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Raspberry Pi Performance Issues

**Solutions:**

1. **Use ARM-optimized image** (already configured in Dockerfile)

2. **Reduce concurrent requests in Google Sheets:**
   - Avoid too many STOCKPRICE() calls at once
   - Use STOCKPRICES() for bulk queries instead

3. **Monitor system:**
   ```bash
   htop  # Install with: sudo apt install htop
   ```

4. **Consider caching** (future enhancement)

### SSL Certificate Issues

**Issue:** HTTPS not working or certificate errors

**Solutions:**

1. **Renew certificate on Synology:**
   - Control Panel → Security → Certificate
   - Renew or re-issue certificate

2. **Use Let's Encrypt:**
   - Synology supports automatic Let's Encrypt certificates
   - Control Panel → Security → Certificate → Add

3. **Check certificate validity:**
   ```bash
   openssl s_client -connect finance.yourdomain.com:443 -servername finance.yourdomain.com
   ```

---

## Security Best Practices

1. **Keep API keys secret**
   - Never commit `.env` to git
   - Use different keys for dev/prod

2. **Regular updates**
   - Update Pi OS: `sudo apt update && sudo apt upgrade`
   - Update Docker images: `docker-compose pull`

3. **Monitor logs**
   - Check for unusual activity
   - Set up log rotation

4. **Firewall rules**
   ```bash
   # On Pi, only allow connections from Synology
   sudo ufw allow from 192.168.1.X to any port 8000
   sudo ufw enable
   ```

5. **Backup configuration**
   - Regularly backup `.env` file
   - Document your setup

---

## Getting Help

If you encounter issues not covered here:

1. Check container logs: `docker-compose logs -f`
2. Test API directly: `curl -v http://localhost:8000/health`
3. Review yfinance issues: https://github.com/ranaroussi/yfinance/issues
4. Check FastAPI docs: https://fastapi.tiangolo.com/

---

**Deployment complete! 🎉**

Your Pi Finance API should now be running securely on your Raspberry Pi, accessible via HTTPS through your Synology reverse proxy.

