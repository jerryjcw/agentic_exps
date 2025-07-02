#!/usr/bin/env python3
"""
Financial Tools for Google ADK

This module provides financial analysis tools that can be used with Google ADK agents:
1. get_earnings_report - Gets earnings data for the last 4 quarters for companies in US, UK, Germany, France
2. get_company_news - Gets the most recent N news articles for a company by name or stock symbol
"""

import requests
import json
import re
import os
from typing import Dict, List, Any
from datetime import datetime
from urllib.parse import quote

# import .env file
from dotenv import load_dotenv

# load .env file under basics 
load_dotenv()

# Import Google search function for news search
try:
    from tools import google_search
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from tools import google_search
    except ImportError:
        # Fallback - define a simple search function
        def google_search(query: str, num_results: int = 5) -> Dict[str, str]:
            return {
                "status": "error",
                "error_message": "Google search function not available"
            }

def get_earnings_report(company_symbol: str, market: str = "US") -> Dict[str, Any]:
    """
    Gets earnings report data for the last 4 quarters for a given company in JSON format.
    
    This tool retrieves key earnings metrics including revenue, earnings per share (EPS),
    net income, and other financial indicators for companies listed on major exchanges
    in the US, UK, Germany, and France.
    
    Args:
        company_symbol (str): The stock ticker symbol (e.g., "AAPL", "MSFT", "BMW.DE")
        market (str): The market/country ("US", "UK", "Germany", "France") - defaults to "US"
        
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: JSON string with structured earnings data if successful
            - data: Parsed earnings data as dict (for programmatic access)
            - error_message: Error description if status is "error"
    """
    try:
        # Normalize market input
        market = market.upper().strip()
        symbol = company_symbol.upper().strip()
        
        # Market-specific symbol handling
        market_info = _get_market_info(market, symbol)
        if market_info["status"] == "error":
            return market_info
            
        # Use Alpha Vantage API for earnings data (free tier available)
        # Note: For production use, you should get your own API key
        print(f"Checking earnings API key: {os.environ.get('EARNINGS_API_KEY')}")
        api_key = os.environ["EARNINGS_API_KEY"]  # Demo key with limited requests
        base_url = "https://www.alphavantage.co/query"
        
        # Get quarterly earnings data
        params = {
            "function": "EARNINGS",
            "symbol": symbol,
            "apikey": api_key
        }
        
        headers = {
            "User-Agent": "Financial-Tool/1.0"
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        print(f"!!!!!!!!!!!!!!!! The response status code is: {response.status_code}, response text: {response.text}")

        if response.status_code == 200:
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                return _try_alternative_source(symbol, market)
            elif "Note" in data:
                return {
                    "status": "error", 
                    "error_message": "API rate limit exceeded. Please try again later."
                }
            
            # Parse earnings data
            if "quarterlyEarnings" in data:
                quarterly_data = data["quarterlyEarnings"][:4]  # Last 4 quarters
                
                if quarterly_data:
                    earnings_json = _format_earnings_json(symbol, market_info, quarterly_data)
                    return {
                        "status": "success",
                        "report": json.dumps(earnings_json, indent=2),
                        "data": earnings_json
                    }
                else:
                    return {
                        "status": "error",
                        "error_message": f"No earnings data available for {symbol} on {market_info['market_name']} market"
                    }
            else:
                return _try_alternative_source(symbol, market)
        else:
            print(f'An error occurred: {response.status_code} - {response.text}')
            return _try_alternative_source(symbol, market)
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request timed out. Please check your internet connection and try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Network error occurred: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting earnings data: {str(e)}"
        }


def get_company_news(company_identifier: str, num_articles: int = 3, market: str = "US") -> Dict[str, Any]:
    """
    Gets the most recent N news articles for a company by name or stock symbol.
    
    This tool retrieves recent news articles about a company from various news sources.
    It supports both company names (e.g., "Apple", "BMW") and stock symbols (e.g., "AAPL", "BMW.DE").
    
    Args:
        company_identifier (str): Company name or stock symbol (e.g., "Apple", "AAPL", "BMW", "BMW.DE")
        num_articles (int): Number of articles to retrieve (default: 3, max: 10)
        market (str): The market/country ("US", "UK", "Germany", "France") - defaults to "US"
        
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: JSON string with structured news data if successful
            - data: Parsed news data as dict (for programmatic access)
            - error_message: Error description if status is "error"
    """
    try:
        # Validate and limit num_articles
        num_articles = max(1, min(10, num_articles))
        
        # Clean and normalize company identifier
        company_identifier = company_identifier.strip()
        
        print(f"🔍 Searching for news about: {company_identifier}")
        
        # Use Google search only with simple search terms
        news_data = _search_google_news(company_identifier, num_articles)
        
        if news_data["status"] == "success" and news_data["articles"]:
            news_json = _format_news_json(company_identifier, market, news_data["articles"][:num_articles])
            return {
                "status": "success",
                "report": json.dumps(news_json, indent=2),
                "data": news_json
            }
        else:
            # Return proper error when no news sources are available
            return {
                "status": "error", 
                "error_message": (
                    f"Unable to retrieve news for {company_identifier}. This could be due to:\n"
                    f"• News API rate limits or service unavailability\n"
                    f"• Network connectivity issues\n"
                    f"• Company identifier not recognized by news sources\n"
                    f"Please verify the company name/symbol and try again later."
                )
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting news for {company_identifier}: {str(e)}"
        }


def _search_google_news(company_identifier: str, num_articles: int) -> Dict[str, Any]:
    """Search for company news using Google search only."""
    try:
        # Create simple search query with stock symbol and "news"
        search_query = f"{company_identifier} news"
        
        # Use Google search function
        search_result = google_search(search_query, num_articles)
        
        if search_result["status"] == "success":
            # Parse Google search results into news format
            articles = _parse_google_search_results(search_result["report"], company_identifier)
            return {
                "status": "success",
                "articles": articles[:num_articles]
            }
        else:
            return {
                "status": "error",
                "error_message": search_result.get("error_message", "Google search failed")
            }
    except Exception as e:
        return {
            "status": "error", 
            "error_message": f"News search failed: {str(e)}"
        }


def _parse_google_search_results(search_report: str, company_identifier: str) -> List[Dict]:
    """Parse Google search results into news article format."""
    articles = []
    
    try:
        # Split the search report into individual results
        lines = search_report.split('\n')
        current_article = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - if we have a complete article, add it
                if current_article.get('title') and current_article.get('url'):
                    articles.append(current_article)
                    current_article = {}
                continue
                
            # Look for numbered results (e.g., "1. **Title**")
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                # If we have a previous article, save it
                if current_article.get('title') and current_article.get('url'):
                    articles.append(current_article)
                    current_article = {}
                
                # Extract title (remove markdown and numbering)
                title = line.split('.', 1)[1].strip()
                title = title.replace('**', '').strip()
                if title:
                    current_article['title'] = title
                    
            # Look for URLs (lines that start with http)
            elif line.startswith('http'):
                current_article['url'] = line
                
            # Look for descriptions (other lines that aren't empty)
            elif line and not line.startswith('Search Results'):
                if 'description' not in current_article:
                    current_article['description'] = line
                else:
                    current_article['description'] += ' ' + line
        
        # Don't forget the last article
        if current_article.get('title') and current_article.get('url'):
            articles.append(current_article)
        
        # Fill in missing fields and clean up
        for article in articles:
            article.setdefault('description', f'News article about {company_identifier}')
            article.setdefault('published_at', datetime.now().isoformat())
            article.setdefault('source', 'Google Search')
            article.setdefault('author', 'Unknown')
            
            # Truncate description if too long
            if len(article['description']) > 200:
                article['description'] = article['description'][:200] + '...'
    
    except Exception as e:
        print(f"Error parsing Google search results: {e}")
    
    return articles


def _format_news_json(company_identifier: str, market: str, articles: List[Dict]) -> Dict[str, Any]:
    """Format news articles into JSON structure."""
    news_json = {
        "company": {
            "identifier": company_identifier,
            "market": market
        },
        "report_metadata": {
            "generated_on": datetime.now().isoformat(),
            "data_source": "news_apis",
            "articles_count": len(articles),
            "search_query": company_identifier
        },
        "news_articles": []
    }
    
    for i, article in enumerate(articles):
        article_data = {
            "rank": i + 1,
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "published_at": article.get("published_at", ""),
            "source": article.get("source", ""),
            "author": article.get("author", "")
        }
        news_json["news_articles"].append(article_data)
    
    return news_json




def _get_market_info(market: str, symbol: str) -> Dict[str, str]:
    """Get market-specific information and validate symbol format."""
    market_configs = {
        "US": {
            "market_name": "United States (NASDAQ/NYSE)",
            "suffix": "",
            "currency": "USD",
            "examples": ["AAPL", "MSFT", "GOOGL", "TSLA"]
        },
        "UK": {
            "market_name": "United Kingdom (LSE)",
            "suffix": ".L",
            "currency": "GBP", 
            "examples": ["BARC.L", "BP.L", "SHEL.L", "AZN.L"]
        },
        "GERMANY": {
            "market_name": "Germany (XETRA)",
            "suffix": ".DE",
            "currency": "EUR",
            "examples": ["BMW.DE", "SAP.DE", "SIE.DE", "ALV.DE"]
        },
        "FRANCE": {
            "market_name": "France (Euronext Paris)",
            "suffix": ".PA",
            "currency": "EUR",
            "examples": ["MC.PA", "OR.PA", "AI.PA", "SAN.PA"]
        }
    }
    
    if market not in market_configs:
        return {
            "status": "error",
            "error_message": f"Unsupported market '{market}'. Supported markets: {', '.join(market_configs.keys())}"
        }
    
    config = market_configs[market]
    
    # Add market suffix if not present (except for US)
    if market != "US" and not symbol.endswith(config["suffix"]):
        symbol = f"{symbol}{config['suffix']}"
    
    return {
        "status": "success",
        "market_name": config["market_name"],
        "currency": config["currency"],
        "symbol": symbol,
        "examples": config["examples"]
    }


def _format_earnings_json(symbol: str, market_info: Dict, quarterly_data: List[Dict]) -> Dict[str, Any]:
    """Format earnings data into JSON structure."""
    quarters = []
    
    for i, quarter in enumerate(quarterly_data):
        quarter_data = {
            "quarter": i + 1,
            "fiscal_date_ending": quarter.get("fiscalDateEnding", None),
            "reported_date": quarter.get("reportedDate", None),
            "reported_eps": _parse_number(quarter.get("reportedEPS")),
            "estimated_eps": _parse_number(quarter.get("estimatedEPS")),
            "surprise": _parse_number(quarter.get("surprise")),
            "surprise_percentage": _parse_number(quarter.get("surprisePercentage")),
            "report_time": quarter.get("reportTime", None)
        }
        quarters.append(quarter_data)
    
    # Calculate quarter-over-quarter EPS growth instead of revenue growth
    quarter_over_quarter_eps_growth = None
    if len(quarters) >= 2:
        try:
            latest_eps = quarters[0]["reported_eps"]
            previous_eps = quarters[1]["reported_eps"]
            
            if latest_eps and previous_eps and latest_eps > 0 and previous_eps > 0:
                quarter_over_quarter_eps_growth = round(((latest_eps - previous_eps) / previous_eps) * 100, 2)
        except (ValueError, TypeError):
            pass
    
    # Calculate year-over-year EPS growth if we have 4 quarters
    year_over_year_eps_growth = None
    if len(quarters) == 4:
        try:
            latest_eps = quarters[0]["reported_eps"]
            year_ago_eps = quarters[3]["reported_eps"]
            
            if latest_eps and year_ago_eps and latest_eps > 0 and year_ago_eps > 0:
                year_over_year_eps_growth = round(((latest_eps - year_ago_eps) / year_ago_eps) * 100, 2)
        except (ValueError, TypeError):
            pass
    
    earnings_json = {
        "company": {
            "symbol": symbol,
            "market": market_info["market_name"],
            "currency": market_info["currency"]
        },
        "report_metadata": {
            "generated_on": datetime.now().isoformat(),
            "data_source": "financial_apis",
            "quarters_included": len(quarters)
        },
        "quarterly_earnings": quarters,
        "analysis": {
            "quarter_over_quarter_eps_growth_percent": quarter_over_quarter_eps_growth,
            "year_over_year_eps_growth_percent": year_over_year_eps_growth
        }
    }
    
    return earnings_json


def _parse_number(value) -> float:
    """Parse string/number value to float, return None if invalid."""
    if value == "N/A" or value is None or value == "":
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _format_number(value) -> str:
    """Format large numbers in a readable way."""
    if value == "N/A" or value is None:
        return "N/A"
    
    try:
        num = float(value)
        if num >= 1_000_000_000:
            return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num/1_000:.2f}K"
        else:
            return f"${num:.2f}"
    except (ValueError, TypeError):
        return str(value)


def _try_alternative_source(symbol: str, market: str) -> Dict[str, str]:
    """Try alternative data source when primary API fails."""
    try:
        # Try Yahoo Finance API as an alternative (free and more reliable)
        yahoo_symbol = _convert_to_yahoo_symbol(symbol, market)
        base_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yahoo_symbol}"
        params = {
            "modules": "earnings,financialData,defaultKeyStatistics"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if "quoteSummary" in data and data["quoteSummary"]["result"]:
                result_data = data["quoteSummary"]["result"][0]
                
                if "earnings" in result_data and result_data["earnings"]:
                    earnings_data = result_data["earnings"]
                    earnings_json = _format_yahoo_earnings_json(symbol, market, earnings_data)
                    return {
                        "status": "success",
                        "report": json.dumps(earnings_json, indent=2),
                        "data": earnings_json
                    }
        
        # If all APIs fail, return proper error
        return {
            "status": "error",
            "error_message": (
                f"Unable to retrieve earnings data for {symbol}. This could be due to:\n"
                f"• Invalid or non-existent ticker symbol\n"
                f"• Company not listed on {market} market\n"
                f"• API rate limits or service unavailability\n"
                f"• Network connectivity issues\n"
                f"Please verify the symbol format and try again later."
            )
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error retrieving earnings data for {symbol}: {str(e)}"
        }


def _convert_to_yahoo_symbol(symbol: str, market: str) -> str:
    """Convert symbol to Yahoo Finance format."""
    # Yahoo Finance uses different suffixes
    symbol_clean = symbol.replace(".DE", "").replace(".L", "").replace(".PA", "")
    
    if market == "GERMANY":
        return f"{symbol_clean}.DE"
    elif market == "UK":
        return f"{symbol_clean}.L"
    elif market == "FRANCE":
        return f"{symbol_clean}.PA"
    else:  # US
        return symbol_clean


def _format_yahoo_earnings_json(symbol: str, market: str, earnings_data: Dict) -> Dict[str, Any]:
    """Format earnings data from Yahoo Finance API into JSON."""
    quarters = []
    
    # Get quarterly data if available
    if "financialsChart" in earnings_data:
        quarterly = earnings_data["financialsChart"].get("quarterly", [])
        
        for i, quarter in enumerate(quarterly[:4]):  # Last 4 quarters
            quarter_data = {
                "quarter": i + 1,
                "date": quarter.get("date"),
                "revenue": _parse_number(quarter.get("revenue", {}).get("raw")),
                "earnings": _parse_number(quarter.get("earnings", {}).get("raw"))
            }
            quarters.append(quarter_data)
    
    market_info = _get_market_info(market, symbol)
    
    earnings_json = {
        "company": {
            "symbol": symbol,
            "market": market,
            "currency": market_info.get("currency", "USD")
        },
        "report_metadata": {
            "generated_on": datetime.now().isoformat(),
            "data_source": "yahoo_finance",
            "quarters_included": len(quarters)
        },
        "quarterly_earnings": quarters,
        "analysis": {}
    }
    
    return earnings_json





# Import FunctionTool for Google ADK compatibility
try:
    from google.adk.tools import FunctionTool
    
    # Wrap functions with FunctionTool for Google ADK agent usage
    earnings_report_tool = FunctionTool(get_earnings_report)
    company_news_tool = FunctionTool(get_company_news)
    
    # Tool registry for easy import
    FINANCIAL_TOOLS = [
        earnings_report_tool,
        company_news_tool
    ]
    
    # Also provide the raw functions for direct testing
    RAW_FINANCIAL_FUNCTIONS = [
        get_earnings_report,
        get_company_news
    ]
    
except ImportError:
    # If Google ADK is not available, provide empty lists
    FINANCIAL_TOOLS = []
    RAW_FINANCIAL_FUNCTIONS = [get_earnings_report]
    print("Warning: Google ADK not available. FunctionTool wrappers not created.")


if __name__ == "__main__":
    """Test the financial tools directly"""
    print("Testing Financial Tools")
    print("=" * 40)
    
    # Test cases for different markets
    earnings_test_cases = [
        ("AAPL", "US", "Apple Inc."),
        ("MSFT", "US", "Microsoft Corporation"),
        ("BMW.DE", "Germany", "BMW Group"),
        ("BARC.L", "UK", "Barclays PLC")
    ]
    
    news_test_cases = [
        ("AAPL", "US", "Apple Inc.", 3),
        ("BMW", "Germany", "BMW Group", 2),
        ("Microsoft", "US", "Microsoft Corporation", 3)
    ]
    
    print("\n1. Testing Earnings Reports:")
    print("=" * 40)
    
    for symbol, market, company_name in earnings_test_cases:
        print(f"\n📊 Testing {company_name} ({symbol}) in {market} market:")
        print("-" * 60)
        
        # Test real API only
        result = get_earnings_report(symbol, market)
        
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            if 'data' in result:
                data = result['data']
                company_name = data['company'].get('name', 'N/A')
                print(f"Company: {company_name} ({data['company']['symbol']})")
                print(f"Market: {data['company']['market']}")
                print(f"Currency: {data['company']['currency']}")
                print(f"Quarters: {data['report_metadata']['quarters_included']}")
        else:
            print(f"Error: {result['error_message']}")
        
        print("-" * 60)
    
    print("\n2. Testing Company News:")
    print("=" * 40)
    
    for company, market, company_name, num_articles in news_test_cases:
        print(f"\n📰 Testing {company_name} ({company}) - {num_articles} articles:")
        print("-" * 60)
        
        # Test real API only
        result = get_company_news(company, num_articles, market)
        
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            if 'data' in result:
                data = result['data']
                company_name = data['company'].get('name', 'N/A')
                print(f"Company: {company_name} ({data['company']['identifier']})")
                print(f"Market: {data['company']['market']}")
                print(f"Articles: {data['report_metadata']['articles_count']}")
                print(f"Data Source: {data['report_metadata']['data_source']}")
                print("Sample articles:")
                for i, article in enumerate(data['news_articles'][:2], 1):
                    print(f"  {i}. {article['title']}")
                    print(f"     Source: {article['source']} | Date: {article['published_at']}")
        else:
            print(f"Error: {result['error_message']}")
        
        print("-" * 60)
    
    # Test FunctionTool wrapper if available
    if FINANCIAL_TOOLS:
        print(f"\n3. Testing FunctionTool Wrappers:")
        print("=" * 40)
        print(f"✅ Financial FunctionTool wrappers created:")
        print(f"   • earnings_report_tool: {type(earnings_report_tool)}")
        print(f"   • company_news_tool: {type(company_news_tool)}")
        print(f"   • FINANCIAL_TOOLS has {len(FINANCIAL_TOOLS)} tools ready for Google ADK agent")
    else:
        print(f"\n⚠️  Google ADK not available - raw functions only")
    