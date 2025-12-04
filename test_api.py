#!/usr/bin/env python3
"""
Test script for Pi Finance API
Run this to verify your API is working correctly
"""

import sys
import os
import requests
from typing import Optional

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text: str):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text: str):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text: str):
    """Print info message"""
    print(f"ℹ {text}")

def test_health_check() -> bool:
    """Test the health check endpoint (no auth required)"""
    print_header("Test 1: Health Check (No Auth)")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_root_endpoint() -> bool:
    """Test the root endpoint"""
    print_header("Test 2: Root Endpoint")
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Root endpoint: {data.get('name')} v{data.get('version')}")
            return True
        else:
            print_error(f"Root endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Root endpoint failed: {str(e)}")
        return False

def test_auth_required() -> bool:
    """Test that authentication is required"""
    print_header("Test 3: Authentication Required")
    try:
        response = requests.get(f"{API_URL}/quote/AAPL", timeout=5)
        if response.status_code == 401:
            print_success("Authentication correctly required (401 Unauthorized)")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Auth test failed: {str(e)}")
        return False

def test_stock_quote(api_key: str) -> bool:
    """Test getting a stock quote"""
    print_header("Test 4: Get Stock Quote (AAPL)")
    try:
        headers = {"X-API-Key": api_key}
        response = requests.get(f"{API_URL}/quote/AAPL", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Quote retrieved: {data.get('symbol')} @ ${data.get('price')}")
            print_info(f"  Currency: {data.get('currency')}")
            print_info(f"  Change: {data.get('change')} ({data.get('change_percent')}%)")
            return True
        elif response.status_code == 403:
            print_error("Authentication failed - Invalid API key")
            return False
        else:
            print_error(f"Quote request failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Quote request failed: {str(e)}")
        return False

def test_multiple_quotes(api_key: str) -> bool:
    """Test getting multiple quotes"""
    print_header("Test 5: Get Multiple Quotes")
    try:
        headers = {"X-API-Key": api_key}
        symbols = "AAPL,MSFT,GOOGL"
        response = requests.get(
            f"{API_URL}/quotes",
            params={"symbols": symbols},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            print_success(f"Retrieved {len(quotes)} quotes")
            for quote in quotes:
                if 'error' not in quote:
                    print_info(f"  {quote.get('symbol')}: ${quote.get('price')}")
            return True
        else:
            print_error(f"Multiple quotes failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Multiple quotes failed: {str(e)}")
        return False

def test_company_info(api_key: str) -> bool:
    """Test getting company information"""
    print_header("Test 6: Get Company Info (AAPL)")
    try:
        headers = {"X-API-Key": api_key}
        response = requests.get(f"{API_URL}/info/AAPL", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Company info retrieved: {data.get('name')}")
            print_info(f"  Sector: {data.get('sector')}")
            print_info(f"  Industry: {data.get('industry')}")
            return True
        else:
            print_error(f"Company info failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Company info failed: {str(e)}")
        return False

def test_historical_data(api_key: str) -> bool:
    """Test getting historical data"""
    print_header("Test 7: Get Historical Data")
    try:
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "symbol": "AAPL",
            "period": "5d",
            "interval": "1d"
        }
        response = requests.post(
            f"{API_URL}/history",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            hist_data = data.get('data', [])
            print_success(f"Historical data retrieved: {len(hist_data)} data points")
            if hist_data:
                latest = hist_data[-1]
                print_info(f"  Latest: {latest.get('date')} @ ${latest.get('close')}")
            return True
        else:
            print_error(f"Historical data failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Historical data failed: {str(e)}")
        return False

def main():
    """Main test runner"""
    print_header("Pi Finance API Test Suite")
    print_info(f"API URL: {API_URL}")
    
    # Check if API key is provided
    if not API_KEY:
        print_error("API_KEY environment variable not set!")
        print_info("Set it with: export API_KEY='your-api-key'")
        print_info("Or get it from your .env file")
        print("")
        
        # Try to read from .env file
        if os.path.exists(".env"):
            print_info("Attempting to read API key from .env file...")
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("API_KEYS="):
                            key = line.split("=", 1)[1].strip()
                            # Get first key if multiple
                            global API_KEY
                            API_KEY = key.split(",")[0].strip()
                            print_success(f"Found API key in .env file")
                            break
            except Exception as e:
                print_error(f"Could not read .env file: {str(e)}")
    
    if not API_KEY:
        print_error("No API key available. Skipping authenticated tests.")
        print("")
    else:
        print_info(f"API Key: {API_KEY[:8]}...")
        print("")
    
    # Run tests
    results = []
    
    # Tests that don't require auth
    results.append(("Health Check", test_health_check()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Auth Required", test_auth_required()))
    
    # Tests that require auth
    if API_KEY:
        results.append(("Stock Quote", test_stock_quote(API_KEY)))
        results.append(("Multiple Quotes", test_multiple_quotes(API_KEY)))
        results.append(("Company Info", test_company_info(API_KEY)))
        results.append(("Historical Data", test_historical_data(API_KEY)))
    
    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print("")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)

