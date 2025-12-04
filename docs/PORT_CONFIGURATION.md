# Port Configuration Guide

The Pi Finance API port is fully configurable to avoid conflicts with other services on your Raspberry Pi.

## Default Port

By default, the API runs on **port 8080** (changed from 8000 to avoid common conflicts).

## Changing the Port

### Method 1: Edit .env file (Recommended)

Edit your `.env` file and change the `API_PORT` value:

```bash
nano .env
```

Change this line:
```env
API_PORT=8080
```

To your desired port:
```env
API_PORT=9000  # or any available port
```

### Method 2: Set environment variable

```bash
export API_PORT=9000
./run_server.sh
```

### Method 3: For Docker

The docker-compose.yml automatically reads the API_PORT from .env:

```bash
# Edit .env
nano .env
# Change API_PORT=8080 to your desired port

# Restart container
docker-compose down
docker-compose up -d
```

## Port Mapping in Docker

The docker-compose.yml maps:
- **External port**: `${API_PORT}` (from .env, defaults to 8080)
- **Internal port**: `8000` (inside container, always the same)

Example:
```yaml
ports:
  - "${API_PORT:-8080}:8000"
```

This means if `API_PORT=9000` in .env:
- Access API at: `http://raspberry-pi-ip:9000`
- Inside container, it still runs on port 8000

## Finding Available Ports

To check if a port is in use:

```bash
# Check if port 8080 is in use
lsof -i :8080

# Find what's using a port
sudo netstat -tulpn | grep :8080

# List all listening ports
sudo netstat -tulpn | grep LISTEN
```

Common ports to avoid:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 3000 (Node.js apps)
- 5000 (Flask default)
- 8000 (Django default)
- 8080 (Common alternative HTTP)

## Update Synology Reverse Proxy

After changing the port, update your Synology reverse proxy configuration:

1. **Synology Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Edit the "Pi Finance API" rule
3. **Destination** → **Port**: Change to your new port number
4. **Save**

## Testing Different Ports

```bash
# Start on different ports
API_PORT=8080 ./run_server.sh
API_PORT=9000 ./run_server.sh
API_PORT=3001 ./run_server.sh

# Test health endpoint
curl http://localhost:8080/health  # original port
curl http://localhost:9000/health  # new port
```

## Update Google Sheets Script

If you change the port and access the API directly (not through reverse proxy), update your Google Apps Script:

```javascript
// Change this line in google-sheets-integration.js
const API_URL = 'https://finance.yourdomain.com';  // Use reverse proxy (port not needed)

// Or if accessing directly:
const API_URL = 'http://raspberry-pi-ip:9000';  // Your new port
```

## Recommended Ports

For home servers, these ports are usually safe:
- **8080** (our default)
- **8081-8089** (common alternatives)
- **3001-3010** (if port 3000 is taken)
- **9000-9999** (usually available)

## Troubleshooting

### "Address already in use"

```bash
# Find what's using your desired port
lsof -i :8080

# Kill the process
kill -9 $(lsof -ti:8080)

# Or choose a different port
echo "API_PORT=9000" >> .env
```

### Port not accessible from outside

Check your firewall:

```bash
# Allow port through ufw (if using)
sudo ufw allow 9000/tcp

# Check if port is listening
netstat -an | grep :9000
```

### Docker container can't bind to port

Make sure no other container or process is using the external port:

```bash
docker ps  # Check other containers
lsof -i :9000  # Check host processes
```

## Quick Reference

| Configuration | File | Value |
|---------------|------|-------|
| Local dev | `.env` | `API_PORT=8080` |
| Docker | `docker-compose.yml` | Uses `${API_PORT}` from .env |
| Startup script | `run_server.sh` | Reads from .env |
| Reverse proxy | Synology | Destination port = API_PORT |

---

**Note**: The internal container port is always 8000. Only the external/exposed port changes.

