from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import yfinance as yf
from datetime import datetime
import logging

from .config import settings
from .auth import verify_api_key
from .models import StockQuote, HistoricalDataRequest, CompanyInfo, ErrorResponse

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
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Get the current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if not current_price:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol: {symbol}"
            )
        
        return StockQuote(
            symbol=symbol.upper(),
            price=current_price,
            currency=info.get('currency'),
            change=info.get('regularMarketChange'),
            change_percent=info.get('regularMarketChangePercent'),
            volume=info.get('volume') or info.get('regularMarketVolume'),
            market_cap=info.get('marketCap'),
            previous_close=info.get('previousClose') or info.get('regularMarketPreviousClose'),
            open=info.get('open') or info.get('regularMarketOpen'),
            day_high=info.get('dayHigh') or info.get('regularMarketDayHigh'),
            day_low=info.get('dayLow') or info.get('regularMarketDayLow'),
        )
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quotes", dependencies=[Depends(verify_api_key)])
async def get_multiple_quotes(symbols: str = Query(..., description="Comma-separated list of symbols")):
    """
    Get quotes for multiple stock symbols.
    
    - **symbols**: Comma-separated list of stock symbols (e.g., AAPL,MSFT,GOOGL)
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed")
        
        results = []
        for symbol in symbol_list:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if current_price:
                    results.append({
                        "symbol": symbol,
                        "price": current_price,
                        "currency": info.get('currency'),
                        "change": info.get('regularMarketChange'),
                        "change_percent": info.get('regularMarketChangePercent'),
                        "volume": info.get('volume') or info.get('regularMarketVolume'),
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


# Import pandas for historical data processing
import pandas as pd


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

