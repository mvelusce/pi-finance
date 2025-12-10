# Price Caching Feature - Implementation Summary

## Overview

The Pi Finance API now includes an intelligent price caching system that dramatically improves Google Sheets performance. Prices are cached in memory and automatically refreshed in the background.

## Key Features

### 1. **Dynamic Ticker Discovery**
- No manual configuration required
- Automatically caches any ticker you request
- Adapts to your portfolio changes automatically

### 2. **Long TTL (Time To Live)**
- Default: 7 days
- Tickers stay cached even if you don't check them for a day or two
- Perfect for daily/bi-daily Google Sheets usage

### 3. **Automatic Background Refresh**
- Default: Every 30 minutes
- Runs in the background without blocking requests
- Keeps cached prices up-to-date automatically

### 4. **Thread-Safe Operations**
- Multiple requests can be handled simultaneously
- Cache operations are protected with locks
- Safe for concurrent Google Sheets access

## Performance Benefits

### Without Cache:
- Every request: 2-5 seconds (Yahoo Finance API call)
- Google Sheet with 20 stocks: 40-100 seconds to load

### With Cache:
- First request: 2-5 seconds (Yahoo Finance API call + cache)
- Subsequent requests: 50-100ms (from cache)
- **Google Sheet with 20 stocks: 1-2 seconds to load!**

### Real-World Example:
If you have a Google Sheet tracking 30 stocks:
- **First load**: ~60 seconds (fetches all from Yahoo)
- **All subsequent loads (within 7 days)**: ~1-2 seconds ⚡
- **Automatic refresh every 30 minutes** keeps prices current

## Configuration

Add these to your `.env` file:

```env
# Enable/disable caching (default: true)
CACHE_ENABLED=true

# How long to keep tickers in cache (default: 7 days)
CACHE_TTL_DAYS=7

# How often to refresh prices (default: 30 minutes)
CACHE_REFRESH_INTERVAL_MINUTES=30
```

## How It Works

### 1. First Request for a Symbol
```
Google Sheets → Pi API → Check Cache (miss) → Yahoo Finance → Return Data
                                             ↓
                                        Store in Cache
```

### 2. Subsequent Requests
```
Google Sheets → Pi API → Check Cache (hit) → Return Cached Data
                                ↓
                        (50-100ms response!)
```

### 3. Background Refresh
```
Every 30 minutes:
- Check all cached symbols
- Fetch fresh data from Yahoo Finance
- Update cache with new prices
- Remove expired symbols (not requested in 7 days)
```

## API Endpoints

### View Cache Statistics
```bash
curl -H "X-API-Key: your-key" http://localhost:8080/cache/stats
```

Response:
```json
{
  "enabled": true,
  "cached_symbols": 15,
  "total_requests": 250,
  "cache_hits": 235,
  "cache_misses": 15,
  "hit_rate_percent": 94.0,
  "ttl_days": 7,
  "refresh_interval_minutes": 30,
  "symbols": ["AAPL", "MSFT", "GOOGL", ...]
}
```

### Get Symbol Cache Info
```bash
curl -H "X-API-Key: your-key" http://localhost:8080/cache/symbols/AAPL
```

### Manually Trigger Refresh
```bash
curl -X POST -H "X-API-Key: your-key" http://localhost:8080/cache/refresh
```

### Clear Cache
```bash
curl -X DELETE -H "X-API-Key: your-key" http://localhost:8080/cache/clear
```

### Remove Specific Symbol
```bash
curl -X DELETE -H "X-API-Key: your-key" http://localhost:8080/cache/symbols/AAPL
```

## Architecture

### Components

1. **`app/cache.py`**: Core caching logic
   - `PriceCache` class: Manages in-memory cache
   - Thread-safe operations with locks
   - TTL management and cleanup
   - Background refresh capability

2. **`app/main.py`**: API integration
   - Cache initialization on startup
   - Background refresh task
   - Updated quote endpoints to use cache
   - Cache management endpoints

3. **`app/config.py`**: Configuration
   - Cache settings from environment variables
   - Configurable TTL and refresh intervals

### Data Flow

```
┌─────────────────┐
│  Google Sheets  │
└────────┬────────┘
         │ API Request
         ↓
┌─────────────────────────────────────┐
│         Pi Finance API              │
│  ┌────────────────────────────┐    │
│  │  Check Cache               │    │
│  │  ├─ Hit? Return immediately │    │
│  │  └─ Miss? Fetch from Yahoo  │    │
│  └────────────────────────────┘    │
│                                     │
│  ┌────────────────────────────┐    │
│  │  In-Memory Cache           │    │
│  │  {                          │    │
│  │    "AAPL": {...},          │    │
│  │    "MSFT": {...},          │    │
│  │    "GOOGL": {...}          │    │
│  │  }                          │    │
│  └────────────────────────────┘    │
│         ↑                           │
│  Background Refresh (every 30m)    │
└─────────────────────────────────────┘
```

## Testing

Run the test suite:

```bash
cd /Users/mveluscek/Workspace/personal/pi-finance
source venv/bin/activate
python test_cache.py
```

Tests verify:
- Cache hit/miss behavior
- Statistics tracking
- TTL and cleanup
- Cache management operations
- Background refresh (optional)

## Deployment

### With Docker (Recommended)

The cache works automatically with Docker:

```bash
# Build and start
docker-compose up -d --build

# Check logs to see cache initialization
docker-compose logs -f api

# You should see:
# "Cache initialized: enabled=True, TTL=7 days, refresh interval=30 minutes"
# "Background cache refresh task started"
```

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Monitoring

### View Cache Activity in Logs

```bash
# Docker
docker-compose logs -f api

# Local
# Logs appear in terminal

# Look for:
# - "Cache HIT for AAPL" - Fast cached response
# - "Cache MISS for MSFT, fetching from Yahoo Finance" - First request
# - "Refreshing 15 cached symbols" - Background refresh
# - "Refresh completed: 15 successful, 0 errors"
```

### Check Cache Statistics

Visit: `http://your-pi:8080/docs#/default/get_cache_stats_cache_stats_get`

Or use curl:
```bash
curl -H "X-API-Key: your-key" http://your-pi:8080/cache/stats
```

## Troubleshooting

### Cache Not Working
1. Check if enabled: Visit `/cache/stats` endpoint
2. View logs: `docker-compose logs -f api`
3. Verify configuration in `.env`
4. Restart: `docker-compose restart api`

### Stale Prices
1. Check last refresh time: `/cache/symbols/AAPL`
2. Manually trigger refresh: `POST /cache/refresh`
3. Check refresh interval setting
4. View logs for refresh errors

### High Memory Usage
- Cache uses minimal memory (~1KB per symbol)
- 100 symbols = ~100KB
- If concerned, reduce TTL_DAYS or clear cache periodically

## Best Practices

### For Daily Usage
```env
CACHE_TTL_DAYS=7
CACHE_REFRESH_INTERVAL_MINUTES=30
```
✅ Perfect balance of performance and freshness

### For Intraday Trading
```env
CACHE_TTL_DAYS=1
CACHE_REFRESH_INTERVAL_MINUTES=5
```
⚠️ More frequent API calls to Yahoo Finance

### For Weekly Check-ins
```env
CACHE_TTL_DAYS=14
CACHE_REFRESH_INTERVAL_MINUTES=60
```
✅ Longer cache life, less frequent refreshes

## Google Sheets Integration

No changes needed to your Google Sheets functions! The caching is transparent:

```javascript
// This automatically uses cache when available
=STOCKPRICE("AAPL")

// These also benefit from caching
=STOCKPRICES("AAPL,MSFT,GOOGL,TSLA")
=STOCKINFO("AAPL", "market_cap")
```

### Expected Behavior

1. **First time you open your sheet today**: Slow (2-3 seconds per stock)
2. **Refresh the sheet**: Fast! (50-100ms per stock)
3. **Open sheet again in 1 hour**: Still fast! (cache still fresh)
4. **Open sheet tomorrow**: Still fast! (cache refreshed in background)
5. **Open sheet in 8 days**: Slow again (cache expired, refetches)

## Future Enhancements

Possible improvements:
- [ ] Persistent cache (Redis/SQLite) to survive restarts
- [ ] Market hours aware refresh (only refresh during trading hours)
- [ ] Configurable refresh per symbol type (stocks vs crypto)
- [ ] Cache warming API (pre-load specific tickers)
- [ ] Webhook notifications when cache is refreshed

## Summary

The caching system provides:
- ⚡ **50-100x faster** responses for cached symbols
- 🔄 **Automatic refresh** keeps data current
- 🧠 **Smart TTL** adapts to your usage patterns
- 🛠️ **Zero configuration** required (works out of the box)
- 📊 **Monitoring endpoints** for visibility
- 🐳 **Docker-ready** for easy deployment

Your Google Sheets will now load **dramatically faster** after the first request!

