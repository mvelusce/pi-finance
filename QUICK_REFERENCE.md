# Pi Finance API - Quick Reference

## 🚀 Quick Start

### Local Development
```bash
# One-line setup
./setup.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key

# Run
uvicorn app.main:app --reload
```

### Docker
```bash
# Create .env file with your API key
cp .env.example .env
nano .env

# Run
docker-compose up --build
```

## 🔑 Generate API Key
```bash
openssl rand -hex 32
```

## 📡 API Endpoints

Base URL: `https://finance.yourdomain.com` or `http://localhost:8000`

All endpoints (except `/` and `/health`) require `X-API-Key` header.

### No Authentication Required
- `GET /` - API info
- `GET /health` - Health check

### Stock Data (Authentication Required)
- `GET /quote/{symbol}` - Single stock quote
  ```bash
  curl -H "X-API-Key: your-key" https://finance.yourdomain.com/quote/AAPL
  ```

- `GET /quotes?symbols=AAPL,MSFT,GOOGL` - Multiple quotes
  ```bash
  curl -H "X-API-Key: your-key" "https://finance.yourdomain.com/quotes?symbols=AAPL,MSFT"
  ```

- `POST /history` - Historical data
  ```bash
  curl -X POST https://finance.yourdomain.com/history \
    -H "X-API-Key: your-key" \
    -H "Content-Type: application/json" \
    -d '{"symbol": "AAPL", "period": "1mo", "interval": "1d"}'
  ```

- `GET /info/{symbol}` - Company information
  ```bash
  curl -H "X-API-Key: your-key" https://finance.yourdomain.com/info/AAPL
  ```

- `GET /dividends/{symbol}?period=1y` - Dividend history
  ```bash
  curl -H "X-API-Key: your-key" "https://finance.yourdomain.com/dividends/AAPL?period=1y"
  ```

## 📊 Google Sheets Integration

### 1. Setup Apps Script
1. Open Google Sheet → **Extensions** → **Apps Script**
2. Copy code from `google-sheets-integration.js`
3. Update `API_URL` and `API_KEY`
4. Save

### 2. Use Functions
```
=STOCKPRICE("AAPL")
=STOCKINFO("MSFT", "market_cap")
=STOCKCHANGE("GOOGL")
=MARKETCAP("TSLA")
=COMPANYNAME("NVDA")
=STOCKPRICES("AAPL,MSFT,GOOGL")
=APISTATUS()
```

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Pull updates
docker-compose pull
docker-compose up -d
```

## 🔧 Raspberry Pi Deployment

### Initial Setup
```bash
# On Pi
git clone <your-repo>
cd pi-finance
cp .env.example .env
nano .env  # Add your API key
docker-compose up -d
```

### Synology Reverse Proxy
**Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**

**Source:**
- Protocol: HTTPS
- Hostname: finance.yourdomain.com
- Port: 443

**Destination:**
- Protocol: HTTP
- Hostname: <raspberry-pi-ip>
- Port: 8000

### Updates
```bash
cd ~/pi-finance
git pull
docker-compose down
docker-compose up -d --build
```

## 🧪 Testing

```bash
# Run test suite
python3 test_api.py

# Or with environment variables
API_URL=http://localhost:8000 API_KEY=your-key python3 test_api.py
```

## 📝 Environment Variables

Create `.env` file:
```env
API_KEYS=your-generated-key-here
CORS_ORIGINS=*
DEBUG=false
```

For Google Sheets, restrict CORS:
```env
CORS_ORIGINS=https://sheets.google.com,https://script.google.com
```

## 🔒 Security

1. **Generate strong API keys**: `openssl rand -hex 32`
2. **Use HTTPS** via reverse proxy
3. **Restrict CORS** to specific domains
4. **Keep `.env` secret** (never commit to git)
5. **Regular updates**: `docker-compose pull && docker-compose up -d`

## 📚 Documentation

- **README.md** - Main documentation
- **DEPLOYMENT.md** - Complete deployment guide
- **DEVELOPMENT.md** - Local development guide
- **google-sheets-integration.js** - Apps Script code

## 🛠️ Troubleshooting

### Container won't start
```bash
docker-compose logs
docker-compose down
docker-compose up --build
```

### 401 Unauthorized
- Check `X-API-Key` header is present
- Verify key matches `.env` file

### 403 Forbidden
- API key is incorrect
- Regenerate key and update `.env`

### Can't access from Google Sheets
- Test API directly: `curl https://finance.yourdomain.com/health`
- Check CORS settings in `.env`
- Verify reverse proxy is working

### Data issues
- Yahoo Finance may have delays
- Check yfinance GitHub for known issues
- Try different symbols to verify API works

## 📦 Project Structure

```
pi-finance/
├── app/                  # Application code
│   ├── main.py          # FastAPI app & endpoints
│   ├── config.py        # Configuration
│   ├── auth.py          # Authentication
│   └── models.py        # Data models
├── .github/workflows/   # GitHub Actions
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose config
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── setup.sh             # Setup script
├── test_api.py          # Test suite
└── *.md                 # Documentation
```

## 🔗 Useful Links

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **FastAPI**: https://fastapi.tiangolo.com/
- **yfinance**: https://github.com/ranaroussi/yfinance

## 💡 Tips

- Use `/docs` endpoint for interactive testing
- Keep logs visible while developing
- Test locally before deploying to Pi
- Use `STOCKPRICES()` for multiple symbols (faster)
- Force Google Sheets refresh by editing cell

## 🎯 Common Use Cases

### Portfolio Tracking
```
Cell A1: AAPL
Cell B1: =STOCKPRICE(A1)
Cell C1: =STOCKCHANGE(A1)
```

### Multiple Stocks
```
=STOCKPRICES("AAPL,MSFT,GOOGL,TSLA,NVDA")
```

### Market Cap Comparison
```
Column A: Symbols
Column B: =MARKETCAP(A2)
```

---

**Need help?** Check the full documentation in README.md, DEPLOYMENT.md, or DEVELOPMENT.md

