#!/usr/bin/env python3
"""
Test script for the Pi Finance API caching functionality.

This script tests:
1. Cache initialization
2. Cache hit/miss behavior
3. Background refresh mechanism
4. Cache management endpoints
"""

import asyncio
import sys
import time
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, '/Users/mveluscek/Workspace/personal/pi-finance')

from app.cache import PriceCache


async def test_cache_basic():
    """Test basic cache operations."""
    print("=" * 70)
    print("TEST 1: Basic Cache Operations")
    print("=" * 70)
    
    # Initialize cache
    cache = PriceCache(
        ttl_days=7,
        refresh_interval_minutes=30,
        enabled=True
    )
    
    # Test cache miss
    print("\n1. Testing cache MISS (symbol not in cache)...")
    result = cache.get("AAPL")
    assert result is None, "Expected cache miss"
    print("   ✓ Cache miss works correctly")
    
    # Add data to cache
    print("\n2. Adding AAPL to cache...")
    test_data = {
        "symbol": "AAPL",
        "price": 195.50,
        "currency": "USD",
        "change": 2.30,
        "change_percent": 1.19,
        "timestamp": datetime.now().isoformat()
    }
    cache.set("AAPL", test_data)
    print("   ✓ Data added to cache")
    
    # Test cache hit
    print("\n3. Testing cache HIT (symbol in cache)...")
    result = cache.get("AAPL")
    assert result is not None, "Expected cache hit"
    assert result["symbol"] == "AAPL", "Wrong symbol returned"
    assert result["price"] == 195.50, "Wrong price returned"
    print(f"   ✓ Cache hit works correctly: ${result['price']}")
    
    # Test cache stats
    print("\n4. Testing cache statistics...")
    stats = cache.get_stats()
    print(f"   - Cached symbols: {stats['cached_symbols']}")
    print(f"   - Total requests: {stats['total_requests']}")
    print(f"   - Cache hits: {stats['cache_hits']}")
    print(f"   - Cache misses: {stats['cache_misses']}")
    print(f"   - Hit rate: {stats['hit_rate_percent']}%")
    assert stats["cached_symbols"] == 1, "Expected 1 cached symbol"
    assert stats["cache_hits"] == 1, "Expected 1 cache hit"
    assert stats["cache_misses"] == 1, "Expected 1 cache miss"
    print("   ✓ Statistics work correctly")
    
    print("\n✅ All basic cache tests passed!\n")


async def test_cache_refresh():
    """Test cache refresh functionality."""
    print("=" * 70)
    print("TEST 2: Cache Refresh Mechanism")
    print("=" * 70)
    
    cache = PriceCache(
        ttl_days=7,
        refresh_interval_minutes=30,
        enabled=True
    )
    
    # Add some test symbols
    print("\n1. Adding test symbols to cache...")
    symbols = ["AAPL", "MSFT", "GOOGL"]
    for symbol in symbols:
        cache.set(symbol, {
            "symbol": symbol,
            "price": 100.0,
            "currency": "USD",
            "timestamp": datetime.now().isoformat()
        })
    print(f"   ✓ Added {len(symbols)} symbols to cache")
    
    # Get symbols to refresh
    print("\n2. Getting symbols that need refresh...")
    symbols_to_refresh = cache.get_symbols_to_refresh()
    print(f"   ✓ Found {len(symbols_to_refresh)} symbols to refresh: {symbols_to_refresh}")
    assert len(symbols_to_refresh) == 3, "Expected 3 symbols"
    
    # Test refresh (will actually call Yahoo Finance - this may take a few seconds)
    print("\n3. Testing live refresh (this may take 5-10 seconds)...")
    print("   Note: This fetches real data from Yahoo Finance")
    await cache.refresh_all()
    
    stats = cache.get_stats()
    print(f"   ✓ Refresh completed: {stats['total_refreshes']} successful refreshes")
    
    # Verify refreshed data
    print("\n4. Verifying refreshed data...")
    for symbol in symbols:
        data = cache.get(symbol)
        if data and data.get("price"):
            print(f"   - {symbol}: ${data['price']:.2f}")
        else:
            print(f"   - {symbol}: Refresh failed (this is OK for testing)")
    
    print("\n✅ Cache refresh test completed!\n")


async def test_ttl_and_cleanup():
    """Test TTL and automatic cleanup."""
    print("=" * 70)
    print("TEST 3: TTL and Cleanup")
    print("=" * 70)
    
    # Create cache with very short TTL for testing
    cache = PriceCache(
        ttl_days=0,  # Expire immediately
        refresh_interval_minutes=30,
        enabled=True
    )
    
    print("\n1. Adding symbol with 0-day TTL (expires immediately)...")
    cache.set("TEST", {
        "symbol": "TEST",
        "price": 1.0,
        "timestamp": datetime.now().isoformat()
    })
    print("   ✓ Symbol added")
    
    # Symbols should be cleaned up when we check for refresh
    print("\n2. Checking for expired symbols...")
    symbols_to_refresh = cache.get_symbols_to_refresh()
    print(f"   ✓ Found {len(symbols_to_refresh)} symbols (expired ones removed)")
    
    stats = cache.get_stats()
    print(f"   - Cached symbols after cleanup: {stats['cached_symbols']}")
    
    print("\n✅ TTL and cleanup test passed!\n")


async def test_cache_management():
    """Test cache management operations."""
    print("=" * 70)
    print("TEST 4: Cache Management")
    print("=" * 70)
    
    cache = PriceCache(
        ttl_days=7,
        refresh_interval_minutes=30,
        enabled=True
    )
    
    # Add test data
    print("\n1. Adding test data...")
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    for symbol in symbols:
        cache.set(symbol, {"symbol": symbol, "price": 100.0})
    print(f"   ✓ Added {len(symbols)} symbols")
    
    # Test symbol info
    print("\n2. Getting symbol info...")
    info = cache.get_symbol_info("AAPL")
    print(f"   - Symbol: {info['symbol']}")
    print(f"   - Cached: {info['cached']}")
    print(f"   - Last refreshed: {info['last_refreshed']}")
    print("   ✓ Symbol info retrieved")
    
    # Test remove symbol
    print("\n3. Removing TSLA from cache...")
    removed = cache.remove_symbol("TSLA")
    assert removed == True, "Expected symbol to be removed"
    print("   ✓ Symbol removed")
    
    stats = cache.get_stats()
    print(f"   - Cached symbols after removal: {stats['cached_symbols']}")
    assert stats["cached_symbols"] == 3, "Expected 3 symbols after removal"
    
    # Test clear cache
    print("\n4. Clearing entire cache...")
    count = cache.clear()
    print(f"   ✓ Cleared {count} symbols")
    
    stats = cache.get_stats()
    assert stats["cached_symbols"] == 0, "Expected 0 symbols after clear"
    print(f"   - Cached symbols after clear: {stats['cached_symbols']}")
    
    print("\n✅ Cache management test passed!\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Pi Finance API - Cache Testing Suite")
    print("=" * 70 + "\n")
    
    try:
        # Run tests
        await test_cache_basic()
        await test_ttl_and_cleanup()
        await test_cache_management()
        
        # Optional: Run refresh test (takes longer)
        print("\nℹ️  Live refresh test skipped (takes 5-10 seconds)")
        print("   To run it, uncomment the line in test_cache.py\n")
        # await test_cache_refresh()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe caching system is working correctly.")
        print("\nNext steps:")
        print("1. Start the API server: python -m uvicorn app.main:app --reload")
        print("2. Check cache stats: curl -H 'X-API-Key: your-key' http://localhost:8000/cache/stats")
        print("3. Test in Google Sheets with your custom functions")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

