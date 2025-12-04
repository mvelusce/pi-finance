/**
 * Pi Finance API - Google Sheets Integration
 * 
 * This script provides custom functions to fetch stock data from your
 * Pi Finance API deployed on your Raspberry Pi.
 * 
 * Setup Instructions:
 * 1. Open your Google Sheet
 * 2. Go to Extensions → Apps Script
 * 3. Paste this entire script
 * 4. Update API_URL and API_KEY with your values
 * 5. Save and authorize the script
 * 6. Use the custom functions in your spreadsheet!
 */

// Configuration - UPDATE THESE VALUES
const API_URL = 'https://finance.yourdomain.com';  // Your API URL (with HTTPS)
const API_KEY = 'your-secret-api-key-here';        // Your API key

// Or use Script Properties for better security:
// const API_KEY = PropertiesService.getScriptProperties().getProperty('API_KEY');

/**
 * Get stock price for a symbol
 * 
 * @param {string} symbol Stock symbol (e.g., "AAPL", "MSFT")
 * @return {number} Current stock price
 * @customfunction
 */
function STOCKPRICE(symbol) {
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  const data = fetchStockData(symbol);
  return data && data.price ? data.price : 'N/A';
}

/**
 * Get specific stock information field
 * 
 * @param {string} symbol Stock symbol
 * @param {string} field Field name (price, change, change_percent, volume, market_cap, open, day_high, day_low)
 * @return {string|number} Requested field value
 * @customfunction
 */
function STOCKINFO(symbol, field) {
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  if (!field) {
    return 'Error: Field required';
  }
  
  const data = fetchStockData(symbol);
  
  if (!data) {
    return 'N/A';
  }
  
  const value = data[field];
  return value !== null && value !== undefined ? value : 'N/A';
}

/**
 * Get stock change percentage
 * 
 * @param {string} symbol Stock symbol
 * @return {number} Change percentage
 * @customfunction
 */
function STOCKCHANGE(symbol) {
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  const data = fetchStockData(symbol);
  return data && data.change_percent ? data.change_percent : 'N/A';
}

/**
 * Get market cap for a stock
 * 
 * @param {string} symbol Stock symbol
 * @return {number} Market capitalization
 * @customfunction
 */
function MARKETCAP(symbol) {
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  const data = fetchStockData(symbol);
  return data && data.market_cap ? data.market_cap : 'N/A';
}

/**
 * Get company name
 * 
 * @param {string} symbol Stock symbol
 * @return {string} Company name
 * @customfunction
 */
function COMPANYNAME(symbol) {
  if (!symbol) {
    return 'Error: Symbol required';
  }
  
  try {
    const url = `${API_URL}/info/${symbol}`;
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
      return data.name || 'N/A';
    }
    
    return 'N/A';
  } catch (e) {
    Logger.log(`Error fetching company name for ${symbol}: ${e.message}`);
    return 'Error';
  }
}

/**
 * Get multiple stock prices at once (faster than multiple STOCKPRICE calls)
 * 
 * @param {string} symbols Comma-separated list of symbols (e.g., "AAPL,MSFT,GOOGL")
 * @return {Array<Array>} 2D array with symbol and price
 * @customfunction
 */
function STOCKPRICES(symbols) {
  if (!symbols) {
    return [['Error: Symbols required']];
  }
  
  try {
    const url = `${API_URL}/quotes?symbols=${encodeURIComponent(symbols)}`;
    const options = {
      'method': 'get',
      'headers': {
        'X-API-Key': API_KEY
      },
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 && data.quotes) {
      const result = [['Symbol', 'Price', 'Change %', 'Volume']];
      
      data.quotes.forEach(quote => {
        if (quote.error) {
          result.push([quote.symbol, 'Error', '', '']);
        } else {
          result.push([
            quote.symbol,
            quote.price || 'N/A',
            quote.change_percent || 'N/A',
            quote.volume || 'N/A'
          ]);
        }
      });
      
      return result;
    }
    
    return [['Error: ' + (data.detail || 'Unknown error')]];
  } catch (e) {
    Logger.log(`Error fetching multiple quotes: ${e.message}`);
    return [['Error: ' + e.message]];
  }
}

/**
 * Get historical data for a stock (returns array for use in charts)
 * 
 * @param {string} symbol Stock symbol
 * @param {string} period Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
 * @param {string} interval Interval (1d, 1wk, 1mo)
 * @return {Array<Array>} 2D array with date and close price
 * @customfunction
 */
function STOCKHISTORY(symbol, period, interval) {
  if (!symbol) {
    return [['Error: Symbol required']];
  }
  
  period = period || '1mo';
  interval = interval || '1d';
  
  try {
    const url = `${API_URL}/history`;
    const payload = {
      symbol: symbol,
      period: period,
      interval: interval
    };
    
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'headers': {
        'X-API-Key': API_KEY
      },
      'payload': JSON.stringify(payload),
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 && data.data) {
      const result = [['Date', 'Open', 'High', 'Low', 'Close', 'Volume']];
      
      data.data.forEach(item => {
        result.push([
          item.date,
          item.open || 'N/A',
          item.high || 'N/A',
          item.low || 'N/A',
          item.close || 'N/A',
          item.volume || 'N/A'
        ]);
      });
      
      return result;
    }
    
    return [['Error: ' + (data.detail || 'No data available')]];
  } catch (e) {
    Logger.log(`Error fetching history for ${symbol}: ${e.message}`);
    return [['Error: ' + e.message]];
  }
}

/**
 * Check if API is accessible
 * 
 * @return {string} API status
 * @customfunction
 */
function APISTATUS() {
  try {
    const url = `${API_URL}/health`;
    const options = {
      'method': 'get',
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 && data.status === 'healthy') {
      return 'Connected ✓';
    }
    
    return 'Error: API not responding';
  } catch (e) {
    return 'Error: Cannot reach API';
  }
}

// ============================================================================
// HELPER FUNCTIONS (Internal use only)
// ============================================================================

/**
 * Helper function to fetch stock data from API
 * @private
 */
function fetchStockData(symbol) {
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
      return data;
    }
    
    Logger.log(`API Error for ${symbol}: ${data.detail}`);
    return null;
  } catch (e) {
    Logger.log(`Error fetching data for ${symbol}: ${e.message}`);
    return null;
  }
}

/**
 * Test function - Run this from the script editor to verify your setup
 */
function testAPIConnection() {
  Logger.log('Testing API connection...');
  Logger.log(`API URL: ${API_URL}`);
  Logger.log(`API Key configured: ${API_KEY ? 'Yes' : 'No'}`);
  
  // Test health endpoint
  try {
    const healthUrl = `${API_URL}/health`;
    const healthResponse = UrlFetchApp.fetch(healthUrl);
    const healthData = JSON.parse(healthResponse.getContentText());
    Logger.log('Health check: ' + JSON.stringify(healthData));
  } catch (e) {
    Logger.log('Health check failed: ' + e.message);
    return;
  }
  
  // Test authenticated endpoint
  try {
    const testSymbol = 'AAPL';
    const quoteUrl = `${API_URL}/quote/${testSymbol}`;
    const options = {
      'method': 'get',
      'headers': {
        'X-API-Key': API_KEY
      }
    };
    
    const quoteResponse = UrlFetchApp.fetch(quoteUrl, options);
    const quoteData = JSON.parse(quoteResponse.getContentText());
    Logger.log(`Quote for ${testSymbol}: ${JSON.stringify(quoteData)}`);
    Logger.log('✓ API connection successful!');
  } catch (e) {
    Logger.log('Quote fetch failed: ' + e.message);
    Logger.log('Please check your API_KEY configuration');
  }
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/*
In your Google Sheet, you can use these formulas:

1. Simple price lookup:
   =STOCKPRICE("AAPL")

2. Get specific fields:
   =STOCKINFO("MSFT", "market_cap")
   =STOCKINFO("GOOGL", "change_percent")
   =STOCKINFO("TSLA", "volume")

3. Quick change percentage:
   =STOCKCHANGE("NVDA")

4. Market cap:
   =MARKETCAP("AAPL")

5. Company name:
   =COMPANYNAME("AAPL")

6. Multiple stocks at once:
   =STOCKPRICES("AAPL,MSFT,GOOGL,TSLA")

7. Historical data:
   =STOCKHISTORY("AAPL", "1mo", "1d")
   =STOCKHISTORY("MSFT", "1y", "1wk")

8. Check API status:
   =APISTATUS()

Tips:
- Functions update automatically when the sheet recalculates
- Force refresh: Edit a cell and press Enter
- View logs: Apps Script editor → Executions
- Test connection: Run testAPIConnection() from script editor
*/

