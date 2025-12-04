# Local Development Guide

## Setup Development Environment

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd pi-finance
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure API key
openssl rand -hex 32

# Edit .env and paste your API key
nano .env  # or use your preferred editor
```

Your `.env` should look like:

```env
API_KEYS=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
CORS_ORIGINS=*
DEBUG=true
```

## Running the API

### Option 1: Direct Python

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run with auto-reload (for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## Testing the API

### Using curl

```bash
# Test health endpoint (no auth required)
curl http://localhost:8000/health

# Test root endpoint
curl http://localhost:8000/

# Test authenticated endpoint - get stock quote
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/quote/AAPL

# Test multiple quotes
curl -H "X-API-Key: your-api-key-here" "http://localhost:8000/quotes?symbols=AAPL,MSFT,GOOGL"

# Test company info
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/info/AAPL

# Test historical data
curl -X POST http://localhost:8000/history \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1mo", "interval": "1d"}'

# Test dividends
curl -H "X-API-Key: your-api-key-here" "http://localhost:8000/dividends/AAPL?period=1y"
```

### Using the Interactive API Docs

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in parameters
5. For authenticated endpoints:
   - Click the 🔒 icon or "Authorize" button at the top
   - Enter your API key in the `X-API-Key` field
   - Click "Authorize"
6. Execute the request

### Using Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY
}

# Get quote
response = requests.get(f"{API_URL}/quote/AAPL", headers=headers)
print(response.json())

# Get multiple quotes
response = requests.get(
    f"{API_URL}/quotes",
    params={"symbols": "AAPL,MSFT,GOOGL"},
    headers=headers
)
print(response.json())

# Get historical data
response = requests.post(
    f"{API_URL}/history",
    json={
        "symbol": "AAPL",
        "period": "1mo",
        "interval": "1d"
    },
    headers=headers
)
print(response.json())
```

## Project Structure

```
pi-finance/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   ├── config.py            # Configuration management
│   ├── auth.py              # API key authentication
│   └── models.py            # Pydantic data models
├── .github/
│   └── workflows/
│       └── docker-build.yml # GitHub Actions workflow
├── .env                      # Environment variables (DO NOT COMMIT)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── README.md                # Main documentation
├── DEPLOYMENT.md            # Deployment guide
├── DEVELOPMENT.md           # This file
└── google-sheets-integration.js  # Google Apps Script code
```

## Code Overview

### app/main.py

Main application file containing:
- FastAPI app initialization
- CORS middleware configuration
- All API endpoints
- Error handling

**Key Endpoints:**
- `GET /` - Root endpoint with API info
- `GET /health` - Health check (no auth)
- `GET /quote/{symbol}` - Get single stock quote
- `GET /quotes` - Get multiple stock quotes
- `POST /history` - Get historical data
- `GET /info/{symbol}` - Get company information
- `GET /dividends/{symbol}` - Get dividend history

### app/config.py

Configuration management using Pydantic Settings:
- Loads environment variables from `.env`
- Provides type-safe configuration
- Handles API keys and CORS origins parsing

### app/auth.py

API key authentication:
- Validates `X-API-Key` header
- Returns 401 if missing
- Returns 403 if invalid

### app/models.py

Pydantic models for request/response validation:
- `StockQuote` - Stock quote response model
- `HistoricalDataRequest` - Historical data request model
- `CompanyInfo` - Company information model
- `ErrorResponse` - Error response model

## Making Changes

### Adding a New Endpoint

1. **Define model in `app/models.py`** (if needed):

```python
class NewModel(BaseModel):
    field1: str
    field2: Optional[int] = None
```

2. **Add endpoint in `app/main.py`**:

```python
@app.get("/new-endpoint", dependencies=[Depends(verify_api_key)])
async def new_endpoint():
    """
    Description of what this endpoint does.
    """
    try:
        # Your logic here
        return {"result": "data"}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

3. **Test it**:

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/new-endpoint
```

4. **Check the auto-generated docs**:

Open http://localhost:8000/docs to see your new endpoint documented.

### Modifying Configuration

1. Add new setting in `app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    new_setting: str = "default_value"
```

2. Add to `.env.example`:

```env
NEW_SETTING=some_value
```

3. Update your `.env` file accordingly.

### Testing with Docker

After making changes:

```bash
# Rebuild and restart
docker-compose down
docker-compose up --build

# Or just rebuild
docker-compose build
docker-compose up -d
```

## Debugging

### Enable Debug Mode

In `.env`:
```env
DEBUG=true
```

This will:
- Show more detailed error messages
- Enable debug logging
- Provide more verbose output

### Check Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f pi-finance-api

# Python (direct run)
# Logs will appear in terminal
```

### Python Debugger

Add breakpoint in code:

```python
import pdb; pdb.set_trace()
```

Or use your IDE's debugger (VS Code, PyCharm, etc.)

### Common Issues

**1. Import Errors**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Port Already in Use**

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.master:app --reload --port 8001
```

**3. Module Not Found**

```bash
# Make sure you're in the right directory
cd pi-finance

# And virtual environment is activated
source venv/bin/activate
```

## Code Quality

### Format Code

```bash
# Install black (formatter)
pip install black

# Format code
black app/
```

### Lint Code

```bash
# Install flake8 (linter)
pip install flake8

# Lint code
flake8 app/
```

### Type Checking

```bash
# Install mypy
pip install mypy

# Type check
mypy app/
```

## Git Workflow

### Before Committing

```bash
# Check what changed
git status

# Review changes
git diff

# Stage changes
git add .

# Commit
git commit -m "Description of changes"
```

### Pushing Changes

```bash
# Push to master (triggers GitHub Actions)
git push origin master

# Or create a branch
git checkout -b feature/new-feature
git push origin feature/new-feature
```

### GitHub Actions

Pushing to `master` or creating a tag will trigger automatic Docker image build:

```bash
# Create and push a version tag
git tag v1.0.1
git push origin v1.0.1
```

This builds and pushes:
- `ghcr.io/your-username/pi-finance:master`
- `ghcr.io/your-username/pi-finance:v1.0.1`
- `ghcr.io/your-username/pi-finance:1.0`
- `ghcr.io/your-username/pi-finance:1`

## Environment Variables Reference

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `API_KEYS` | Comma-separated API keys | - | `key1,key2,key3` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | `https://sheets.google.com` |
| `APP_NAME` | Application name | `Pi Finance API` | `My Finance API` |
| `APP_VERSION` | Application version | `1.0.0` | `1.0.0` |
| `DEBUG` | Debug mode | `false` | `true` or `false` |

## Additional Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **yfinance**: https://github.com/ranaroussi/yfinance
- **Pydantic**: https://docs.pydantic.dev/
- **Uvicorn**: https://www.uvicorn.org/
- **Docker**: https://docs.docker.com/

## Tips

1. **Use virtual environment** - Always activate before working
2. **Check docs** - Visit `/docs` endpoint for interactive API testing
3. **Watch logs** - Keep logs visible while developing
4. **Test changes** - Test locally before pushing
5. **Read yfinance docs** - Understand data source limitations
6. **Keep dependencies updated** - Regularly update `requirements.txt`

## Next Steps

- Add caching for better performance
- Implement rate limiting
- Add more financial data endpoints
- Create unit tests
- Add monitoring/alerting
- Implement request logging

---

Happy coding! 🚀

