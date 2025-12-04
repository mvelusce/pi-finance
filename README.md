# Pi Finance API

A simple and secure Yahoo Finance API wrapper designed for Google Sheets integration. Deploy it on your Raspberry Pi and access financial data from anywhere!

## Features

- 🚀 **Simple REST API** - Easy to use from Google Apps Script
- 🔒 **Secure** - API key authentication to protect your endpoint
- 🐳 **Docker-ready** - Deploy anywhere with Docker
- 🏗️ **Multi-arch support** - Works on Raspberry Pi (ARM) and x64 systems
- 📊 **Rich data** - Stock quotes, historical data, company info, dividends, and more
- 🔄 **Auto-deploy** - GitHub Actions automatically build and push Docker images

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- A valid API key (generate one with: `openssl rand -hex 32`)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pi-finance
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set your API key**
   ```bash
   # Generate a secure API key
   openssl rand -hex 32
   
   # Edit .env and replace 'your-secret-api-key-here' with your generated key
   nano .env
   
   # Optional: Change the port if 8080 is already in use
   # API_PORT=9000
   ```

4. **Install Python dependencies (for local development without Docker)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Run locally**
   ```bash
   # With Docker Compose
   docker-compose up --build
   
   # Or directly with Python (recommended)
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or use the startup script
   ./run_server.sh
   ```

6. **Access the API**
   - API: http://localhost:8080 (or your configured port)
   - Interactive docs: http://localhost:8080/docs
   - Alternative docs: http://localhost:8080/redoc

## Deployment on Raspberry Pi

### Quick Setup (Recommended)

The easiest way to deploy on your Raspberry Pi:

1. **SSH into your Raspberry Pi**
   ```bash
   ssh pi@your-pi-address
   ```

2. **Create a directory and download files**
   ```bash
   mkdir -p ~/pi-finance
   cd ~/pi-finance
   
   # Download docker-compose.yml
   wget -O docker-compose.yml https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/master/docker-compose.yml
   
   # Download .env.example
   wget -O .env.example https://raw.githubusercontent.com/YOUR_USERNAME/pi-finance/master/.env.example
   ```

3. **Create and configure your .env file**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Set your configuration:
   ```env
   # Generate a secure API key
   # Run: openssl rand -hex 32
   API_KEYS=your-generated-secure-key-here
   
   # Change port if 8080 is already in use
   API_PORT=8080
   
   # Restrict CORS for better security (optional)
   CORS_ORIGINS=*
   
   # Your GitHub username (for pulling the Docker image)
   GITHUB_USER=your-github-username
   ```

4. **Start the service**
   ```bash
   docker-compose up -d
   ```

5. **Check logs**
   ```bash
   docker-compose logs -f
   ```

That's it! Your API is now running on `http://raspberry-pi-ip:8080`

### Building from Source (Alternative)

If you prefer to build the image locally:

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pi-finance.git
   cd pi-finance
   ```

2. **Create and configure .env file**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Build and start with local Dockerfile**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d --build
   ```

### Configure Reverse Proxy (Synology NAS)

Since you have a reverse proxy on your Synology NAS:

1. **Access Synology Control Panel** → **Application Portal** → **Reverse Proxy**

2. **Create new reverse proxy rule:**
   - **Source:**
     - Protocol: HTTPS
     - Hostname: finance.yourdomain.com
     - Port: 443
     - Enable HSTS: Yes (optional)
   
   - **Destination:**
     - Protocol: HTTP
     - Hostname: <raspberry-pi-ip>
     - Port: 8000

3. **Save and test** by visiting https://finance.yourdomain.com/health

## API Endpoints

All endpoints (except `/` and `/health`) require the `X-API-Key` header.

### Authentication

Add the header to all requests:
```
X-API-Key: your-secret-api-key-here
```

### Available Endpoints

#### 1. Get Stock Quote
```http
GET /quote/{symbol}
```

Example:
```bash
curl -H "X-API-Key: your-key" https://finance.yourdomain.com/quote/AAPL
```

Response:
```json
{
  "symbol": "AAPL",
  "price": 195.50,
  "currency": "USD",
  "change": 2.30,
  "change_percent": 1.19,
  "volume": 52000000,
  "market_cap": 3024000000000,
  "previous_close": 193.20,
  "open": 194.00,
  "day_high": 196.00,
  "day_low": 193.50,
  "timestamp": "2025-12-03T10:30:00"
}
```

#### 2. Get Multiple Quotes
```http
GET /quotes?symbols=AAPL,MSFT,GOOGL
```

#### 3. Get Historical Data
```http
POST /history
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1mo",
  "interval": "1d"
}
```

#### 4. Get Company Info
```http
GET /info/{symbol}
```

#### 5. Get Dividends
```http
GET /dividends/{symbol}?period=1y
```

#### 6. Health Check (No Auth Required)
```http
GET /health
```

## Using with Google Sheets

### 1. Create Apps Script Function

1. Open your Google Sheet
2. Go to **Extensions** → **Apps Script**
3. Paste the following code:

```javascript
/**
 * Get stock quote from Pi Finance API
 * @param {string} symbol Stock symbol (e.g., "AAPL")
 * @return {number} Current stock price
 * @customfunction
 */
function STOCKPRICE(symbol) {
  const API_URL = 'https://finance.yourdomain.com';
  const API_KEY = 'your-secret-api-key-here';
  
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  try {
    const url = `${API_URL}/quote/${symbol}`;
    const options = {
      'method': 'get',
      'headers': {
        'X-API-Key': API_KEY
      },
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return data.price;
    } else {
      return `Error: ${data.detail}`;
    }
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

/**
 * Get detailed stock information
 * @param {string} symbol Stock symbol
 * @param {string} field Field to return (price, change, volume, etc.)
 * @return {string} Requested field value
 * @customfunction
 */
function STOCKINFO(symbol, field) {
  const API_URL = 'https://finance.yourdomain.com';
  const API_KEY = 'your-secret-api-key-here';
  
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  try {
    const url = `${API_URL}/quote/${symbol}`;
    const options = {
      'method': 'get',
      'headers': {
        'X-API-Key': API_KEY
      },
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return data[field] || 'Field not found';
    } else {
      return `Error: ${data.detail}`;
    }
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
```

### 2. Use in Your Sheet

In any cell, you can now use:
```
=STOCKPRICE("AAPL")
=STOCKINFO("MSFT", "market_cap")
=STOCKINFO("GOOGL", "change_percent")
```

### 3. Script Properties (More Secure)

For better security, store your API key in Script Properties:

1. In Apps Script editor: **Project Settings** → **Script Properties**
2. Add property: `API_KEY` = `your-secret-api-key`
3. Update the script to use:
   ```javascript
   const API_KEY = PropertiesService.getScriptProperties().getProperty('API_KEY');
   ```

## Security Best Practices

1. **Generate Strong API Keys**
   ```bash
   openssl rand -hex 32
   ```

2. **Use HTTPS** - Always access your API via HTTPS (through reverse proxy)

3. **Restrict CORS** - In `.env`, set specific origins:
   ```env
   CORS_ORIGINS=https://sheets.google.com,https://script.google.com
   ```

4. **Keep Keys Secret** - Never commit `.env` file to git

5. **Regular Updates** - Keep Docker image updated:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

6. **Monitor Logs**
   ```bash
   docker-compose logs -f api
   ```

## GitHub Actions Setup

The repository includes GitHub Actions for automatic Docker image building.

### Setup Steps:

1. **Enable GitHub Container Registry**
   - Go to your repo → **Settings** → **Actions** → **General**
   - Under "Workflow permissions", select "Read and write permissions"

2. **Push to master branch or create a tag**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin master
   
   # Or create a version tag
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **Image will be available at:**
   ```
   ghcr.io/<your-username>/pi-finance:master
   ghcr.io/<your-username>/pi-finance:v1.0.0
   ```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Verify environment variables
docker-compose config
```

### API returns 401/403
- Check that X-API-Key header is set correctly
- Verify API_KEYS in .env matches your request header

### Can't access from Google Sheets
- Verify your reverse proxy is working: `curl https://finance.yourdomain.com/health`
- Check CORS settings in `.env`
- Ensure HTTPS is properly configured on your Synology

### Data is stale or incorrect
- Yahoo Finance API sometimes has delays
- Try a different symbol to verify API is working
- Check yfinance library issues: https://github.com/ranaroussi/yfinance

## Development

### Project Structure
```
pi-finance/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration settings
│   ├── auth.py          # Authentication logic
│   └── models.py        # Pydantic models
├── .github/
│   └── workflows/
│       └── docker-build.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Running Tests Locally
```bash
# Install test dependencies
pip install pytest httpx

# Run API in one terminal
uvicorn app.main:app --reload

# Test in another terminal
curl -H "X-API-Key: your-key" http://localhost:8000/quote/AAPL
```

### Making Changes
1. Make your changes to the code
2. Test locally with Docker:
   ```bash
   docker-compose up --build
   ```
3. Commit and push to trigger GitHub Actions
4. Pull the new image on your Pi:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Docker Documentation](https://docs.docker.com/)
- [Google Apps Script Guide](https://developers.google.com/apps-script)

## License

MIT License - Feel free to use and modify as needed!

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs` endpoint
3. Check yfinance GitHub issues for data-related problems
4. Open an issue in this repository

---

**Happy Trading! 📈**

