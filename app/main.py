from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import yfinance as yf
from datetime import datetime
import logging
import asyncio

from .config import settings
from .auth import verify_api_key
from .models import StockQuote, HistoricalDataRequest, CompanyInfo, ErrorResponse
from .cache import initialize_cache, get_cache

# Configure logging
logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A simple Yahoo Finance API wrapper for Google Sheets integration",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task for cache refresh
async def refresh_cache_periodically():
    """Background task to refresh cached prices periodically."""
    cache = get_cache()
    
    while True:
        try:
            await asyncio.sleep(settings.cache_refresh_interval_minutes * 60)
            logger.info("Starting periodic cache refresh")
            await cache.refresh_all()
        except Exception as e:
            logger.error(f"Error in cache refresh task: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize cache and start background refresh task."""
    # Initialize cache
    initialize_cache(
        enabled=settings.cache_enabled,
        ttl_days=settings.cache_ttl_days,
        refresh_interval_minutes=settings.cache_refresh_interval_minutes
    )
    
    logger.info(
        f"Cache initialized: enabled={settings.cache_enabled}, "
        f"TTL={settings.cache_ttl_days} days, "
        f"refresh interval={settings.cache_refresh_interval_minutes} minutes"
    )
    
    # Start background refresh task
    if settings.cache_enabled:
        asyncio.create_task(refresh_cache_periodically())
        logger.info("Background cache refresh task started")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "authentication": "Required - Use X-API-Key header"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint (no authentication required)."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/quote/{symbol}", response_model=StockQuote, dependencies=[Depends(verify_api_key)])
async def get_quote(symbol: str):
    """
    Get current quote for a stock symbol.
    
    - **symbol**: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
    
    Note: This endpoint uses caching. Prices are refreshed automatically every
    30 minutes (configurable). First request for a new symbol may be slower.
    """
    try:
        cache = get_cache()
        symbol_upper = symbol.upper()
        
        # Try to get from cache first
        cached_data = cache.get(symbol_upper)
        
        if cached_data:
            logger.debug(f"Returning cached data for {symbol_upper}")
            return StockQuote(**cached_data)
        
        # Cache miss - fetch from yfinance
        logger.info(f"Cache miss for {symbol_upper}, fetching from Yahoo Finance")
        ticker = yf.Ticker(symbol_upper)
        info = ticker.info
        
        # Get the current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if not current_price:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol: {symbol}"
            )
        
        quote_data = {
            "symbol": symbol_upper,
            "price": current_price,
            "currency": info.get('currency'),
            "change": info.get('regularMarketChange'),
            "change_percent": info.get('regularMarketChangePercent'),
            "volume": info.get('volume') or info.get('regularMarketVolume'),
            "market_cap": info.get('marketCap'),
            "previous_close": info.get('previousClose') or info.get('regularMarketPreviousClose'),
            "open": info.get('open') or info.get('regularMarketOpen'),
            "day_high": info.get('dayHigh') or info.get('regularMarketDayHigh'),
            "day_low": info.get('dayLow') or info.get('regularMarketDayLow'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in cache for future requests
        cache.set(symbol_upper, quote_data)
        
        return StockQuote(**quote_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quotes", dependencies=[Depends(verify_api_key)])
async def get_multiple_quotes(symbols: str = Query(..., description="Comma-separated list of symbols")):
    """
    Get quotes for multiple stock symbols.
    
    - **symbols**: Comma-separated list of stock symbols (e.g., AAPL,MSFT,GOOGL)
    
    Note: This endpoint uses caching for improved performance.
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed")
        
        cache = get_cache()
        results = []
        
        for symbol in symbol_list:
            try:
                # Try cache first
                cached_data = cache.get(symbol)
                
                if cached_data:
                    results.append({
                        "symbol": symbol,
                        "price": cached_data.get("price"),
                        "currency": cached_data.get("currency"),
                        "change": cached_data.get("change"),
                        "change_percent": cached_data.get("change_percent"),
                        "volume": cached_data.get("volume"),
                        "cached": True
                    })
                else:
                    # Cache miss - fetch from yfinance
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    
                    if current_price:
                        quote_data = {
                            "symbol": symbol,
                            "price": current_price,
                            "currency": info.get('currency'),
                            "change": info.get('regularMarketChange'),
                            "change_percent": info.get('regularMarketChangePercent'),
                            "volume": info.get('volume') or info.get('regularMarketVolume'),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Store in cache
                        cache.set(symbol, quote_data)
                        
                        results.append({
                            "symbol": symbol,
                            "price": current_price,
                            "currency": info.get('currency'),
                            "change": info.get('regularMarketChange'),
                            "change_percent": info.get('regularMarketChangePercent'),
                            "volume": info.get('volume') or info.get('regularMarketVolume'),
                            "cached": False
                        })
            except Exception as e:
                logger.warning(f"Error fetching {symbol}: {str(e)}")
                results.append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        return {"quotes": results, "count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching multiple quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/history", dependencies=[Depends(verify_api_key)])
async def get_historical_data(request: HistoricalDataRequest):
    """
    Get historical price data for a stock.
    
    - **symbol**: Stock ticker symbol
    - **period**: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    - **interval**: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    """
    try:
        ticker = yf.Ticker(request.symbol.upper())
        hist = ticker.history(period=request.period, interval=request.interval)
        
        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for {request.symbol}"
            )
        
        # Convert to dict with date as string
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(row['Open']) if not pd.isna(row['Open']) else None,
                "high": float(row['High']) if not pd.isna(row['High']) else None,
                "low": float(row['Low']) if not pd.isna(row['Low']) else None,
                "close": float(row['Close']) if not pd.isna(row['Close']) else None,
                "volume": int(row['Volume']) if not pd.isna(row['Volume']) else None,
            })
        
        return {
            "symbol": request.symbol.upper(),
            "period": request.period,
            "interval": request.interval,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info/{symbol}", response_model=CompanyInfo, dependencies=[Depends(verify_api_key)])
async def get_company_info(symbol: str):
    """
    Get company information for a stock symbol.
    
    - **symbol**: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if not info or len(info) < 3:
            raise HTTPException(
                status_code=404,
                detail=f"No company info found for symbol: {symbol}"
            )
        
        return CompanyInfo(
            symbol=symbol.upper(),
            name=info.get('longName') or info.get('shortName'),
            sector=info.get('sector'),
            industry=info.get('industry'),
            website=info.get('website'),
            description=info.get('longBusinessSummary'),
            country=info.get('country'),
            employees=info.get('fullTimeEmployees'),
            market_cap=info.get('marketCap'),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company info for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dividends/{symbol}", dependencies=[Depends(verify_api_key)])
async def get_dividends(symbol: str, period: str = Query(default="1y", description="Period: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max")):
    """
    Get dividend history for a stock symbol.
    
    - **symbol**: Stock ticker symbol
    - **period**: Time period for dividend history
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        dividends = ticker.dividends
        
        if dividends.empty:
            return {
                "symbol": symbol.upper(),
                "period": period,
                "dividends": [],
                "message": "No dividend data available"
            }
        
        # Filter by period if needed
        # Convert to list of dicts
        div_data = []
        for date, value in dividends.items():
            div_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": float(value)
            })
        
        return {
            "symbol": symbol.upper(),
            "dividends": div_data[-100:]  # Limit to last 100 dividends
        }
    except Exception as e:
        logger.error(f"Error fetching dividends for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/cache/stats", dependencies=[Depends(verify_api_key)])
async def get_cache_stats():
    """
    Get cache statistics and information.
    
    Returns information about:
    - Cache hit/miss rates
    - Number of cached symbols
    - Cache configuration
    - List of cached symbols
    """
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/symbols/{symbol}", dependencies=[Depends(verify_api_key)])
async def get_cached_symbol_info(symbol: str):
    """
    Get detailed information about a specific cached symbol.
    
    - **symbol**: Stock ticker symbol
    
    Returns metadata about when the symbol was last requested and refreshed.
    """
    try:
        cache = get_cache()
        info = cache.get_symbol_info(symbol.upper())
        
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} is not in cache"
            )
        
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/refresh", dependencies=[Depends(verify_api_key)])
async def trigger_cache_refresh():
    """
    Manually trigger a cache refresh for all cached symbols.
    
    This is done automatically in the background, but can be triggered
    manually if needed.
    """
    try:
        cache = get_cache()
        
        if not cache.enabled:
            return {
                "message": "Cache is disabled",
                "refreshed": 0
            }
        
        # Trigger refresh in background
        asyncio.create_task(cache.refresh_all())
        
        symbols = cache.get_symbols_to_refresh()
        
        return {
            "message": "Cache refresh triggered",
            "symbols_to_refresh": len(symbols),
            "symbols": symbols
        }
    except Exception as e:
        logger.error(f"Error triggering cache refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear", dependencies=[Depends(verify_api_key)])
async def clear_cache():
    """
    Clear all cached data.
    
    Use this to force fresh data fetches for all symbols.
    """
    try:
        cache = get_cache()
        count = cache.clear()
        
        return {
            "message": "Cache cleared successfully",
            "symbols_removed": count
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/symbols/{symbol}", dependencies=[Depends(verify_api_key)])
async def remove_symbol_from_cache(symbol: str):
    """
    Remove a specific symbol from the cache.
    
    - **symbol**: Stock ticker symbol to remove
    
    The next request for this symbol will fetch fresh data.
    """
    try:
        cache = get_cache()
        removed = cache.remove_symbol(symbol.upper())
        
        if not removed:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} is not in cache"
            )
        
        return {
            "message": f"Symbol {symbol.upper()} removed from cache"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing symbol from cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Import pandas for historical data processing
import pandas as pd


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

