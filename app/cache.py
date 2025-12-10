"""
Price caching module for Pi Finance API

This module provides in-memory caching of stock prices with:
- Dynamic ticker discovery (no static configuration needed)
- Automatic periodic refresh of cached prices
- Configurable TTL and refresh intervals
- Thread-safe operations
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import asyncio
import logging
from threading import Lock
import yfinance as yf

logger = logging.getLogger(__name__)


class PriceCache:
    """
    In-memory cache for stock prices with automatic refresh capabilities.
    
    Features:
    - Tracks recently requested tickers dynamically
    - Periodic background refresh of cached prices
    - Configurable TTL for ticker expiration
    - Thread-safe operations
    """
    
    def __init__(
        self,
        ttl_days: int = 7,
        refresh_interval_minutes: int = 30,
        enabled: bool = True
    ):
        """
        Initialize the price cache.
        
        Args:
            ttl_days: How long to keep a ticker in cache after last request (default: 7 days)
            refresh_interval_minutes: How often to refresh cached prices (default: 30 minutes)
            enabled: Whether caching is enabled (default: True)
        """
        self.enabled = enabled
        self.ttl_days = ttl_days
        self.refresh_interval_minutes = refresh_interval_minutes
        
        # Cache storage: symbol -> price data
        self._cache: Dict[str, dict] = {}
        
        # Metadata: symbol -> {last_requested, last_refreshed}
        self._metadata: Dict[str, dict] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "refreshes": 0,
            "errors": 0
        }
        
        logger.info(
            f"Price cache initialized: enabled={enabled}, "
            f"ttl={ttl_days} days, refresh_interval={refresh_interval_minutes} mins"
        )
    
    def get(self, symbol: str) -> Optional[dict]:
        """
        Get price data from cache.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Cached price data if available and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        symbol = symbol.upper()
        
        with self._lock:
            # Update last requested time
            if symbol not in self._metadata:
                self._metadata[symbol] = {}
            
            self._metadata[symbol]["last_requested"] = datetime.now()
            
            # Check if we have cached data
            if symbol in self._cache:
                self._stats["hits"] += 1
                logger.debug(f"Cache HIT for {symbol}")
                return self._cache[symbol].copy()
            
            self._stats["misses"] += 1
            logger.debug(f"Cache MISS for {symbol}")
            return None
    
    def set(self, symbol: str, data: dict) -> None:
        """
        Store price data in cache.
        
        Args:
            symbol: Stock ticker symbol
            data: Price data to cache
        """
        if not self.enabled:
            return
        
        symbol = symbol.upper()
        
        with self._lock:
            self._cache[symbol] = data
            
            if symbol not in self._metadata:
                self._metadata[symbol] = {}
            
            self._metadata[symbol]["last_refreshed"] = datetime.now()
            self._metadata[symbol]["last_requested"] = datetime.now()
            
            logger.debug(f"Cached data for {symbol}")
    
    def get_symbols_to_refresh(self) -> List[str]:
        """
        Get list of symbols that should be refreshed.
        
        Returns:
            List of symbols that are still within TTL
        """
        if not self.enabled:
            return []
        
        with self._lock:
            now = datetime.now()
            ttl_cutoff = now - timedelta(days=self.ttl_days)
            
            symbols_to_refresh = []
            expired_symbols = []
            
            for symbol, metadata in self._metadata.items():
                last_requested = metadata.get("last_requested")
                
                if last_requested and last_requested > ttl_cutoff:
                    # Symbol is still within TTL, should be refreshed
                    symbols_to_refresh.append(symbol)
                else:
                    # Symbol has expired, mark for removal
                    expired_symbols.append(symbol)
            
            # Clean up expired symbols
            for symbol in expired_symbols:
                logger.info(f"Removing expired symbol from cache: {symbol}")
                self._cache.pop(symbol, None)
                self._metadata.pop(symbol, None)
            
            return symbols_to_refresh
    
    async def refresh_all(self) -> None:
        """
        Refresh all cached symbols with fresh data from Yahoo Finance.
        
        This is called periodically by the background scheduler.
        """
        if not self.enabled:
            return
        
        symbols = self.get_symbols_to_refresh()
        
        if not symbols:
            logger.debug("No symbols to refresh")
            return
        
        logger.info(f"Refreshing {len(symbols)} cached symbols: {', '.join(symbols)}")
        
        # Refresh each symbol
        refreshed_count = 0
        error_count = 0
        
        for symbol in symbols:
            try:
                # Fetch fresh data from yfinance
                data = await self._fetch_fresh_data(symbol)
                
                if data:
                    with self._lock:
                        self._cache[symbol] = data
                        self._metadata[symbol]["last_refreshed"] = datetime.now()
                        self._stats["refreshes"] += 1
                    
                    refreshed_count += 1
                    logger.debug(f"Refreshed {symbol}: ${data.get('price')}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to refresh {symbol}: No data returned")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                self._stats["errors"] += 1
                logger.error(f"Error refreshing {symbol}: {str(e)}")
        
        logger.info(
            f"Refresh completed: {refreshed_count} successful, "
            f"{error_count} errors out of {len(symbols)} symbols"
        )
    
    async def _fetch_fresh_data(self, symbol: str) -> Optional[dict]:
        """
        Fetch fresh price data from Yahoo Finance.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Price data dictionary or None if fetch fails
        """
        try:
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not current_price:
                return None
            
            return {
                "symbol": symbol,
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
        except Exception as e:
            logger.error(f"Error fetching fresh data for {symbol}: {str(e)}")
            return None
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )
            
            return {
                "enabled": self.enabled,
                "cached_symbols": len(self._cache),
                "total_requests": total_requests,
                "cache_hits": self._stats["hits"],
                "cache_misses": self._stats["misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "total_refreshes": self._stats["refreshes"],
                "refresh_errors": self._stats["errors"],
                "ttl_days": self.ttl_days,
                "refresh_interval_minutes": self.refresh_interval_minutes,
                "symbols": list(self._cache.keys()) if self._cache else []
            }
    
    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Get detailed information about a cached symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Symbol metadata or None if not cached
        """
        symbol = symbol.upper()
        
        with self._lock:
            if symbol not in self._cache:
                return None
            
            metadata = self._metadata.get(symbol, {})
            
            return {
                "symbol": symbol,
                "price": self._cache[symbol].get("price"),
                "cached": True,
                "last_requested": metadata.get("last_requested").isoformat() if metadata.get("last_requested") else None,
                "last_refreshed": metadata.get("last_refreshed").isoformat() if metadata.get("last_refreshed") else None,
                "data": self._cache[symbol]
            }
    
    def clear(self) -> int:
        """
        Clear all cached data.
        
        Returns:
            Number of symbols removed
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._metadata.clear()
            logger.info(f"Cache cleared: {count} symbols removed")
            return count
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a specific symbol from cache.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol was removed, False if not in cache
        """
        symbol = symbol.upper()
        
        with self._lock:
            if symbol in self._cache:
                self._cache.pop(symbol, None)
                self._metadata.pop(symbol, None)
                logger.info(f"Removed {symbol} from cache")
                return True
            
            return False


# Global cache instance
_cache_instance: Optional[PriceCache] = None


def get_cache() -> PriceCache:
    """Get the global cache instance."""
    global _cache_instance
    
    if _cache_instance is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    
    return _cache_instance


def initialize_cache(
    enabled: bool = True,
    ttl_days: int = 7,
    refresh_interval_minutes: int = 30
) -> PriceCache:
    """
    Initialize the global cache instance.
    
    Args:
        enabled: Whether caching is enabled
        ttl_days: How long to keep tickers in cache
        refresh_interval_minutes: How often to refresh prices
        
    Returns:
        Initialized PriceCache instance
    """
    global _cache_instance
    
    _cache_instance = PriceCache(
        enabled=enabled,
        ttl_days=ttl_days,
        refresh_interval_minutes=refresh_interval_minutes
    )
    
    return _cache_instance

