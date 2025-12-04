from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class StockQuote(BaseModel):
    """Model for stock quote response."""
    symbol: str
    price: Optional[float] = None
    currency: Optional[str] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    previous_close: Optional[float] = None
    open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HistoricalDataRequest(BaseModel):
    """Request model for historical data."""
    symbol: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    period: str = Field(default="1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")
    interval: str = Field(default="1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")


class CompanyInfo(BaseModel):
    """Model for company information."""
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    employees: Optional[int] = None
    market_cap: Optional[float] = None


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str
    detail: Optional[str] = None

