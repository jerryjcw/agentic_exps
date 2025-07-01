#!/usr/bin/env python3
"""
Google ADK Compatible Tools

This module provides tools that can be used with Google ADK agents:
1. get_current_time - Gets current time for any city worldwide
2. get_temperature - Gets current temperature for a given location
3. google_search - Performs Google search queries
"""

import datetime
import pytz
import requests
import os
from typing import Dict


def get_current_time(city: str) -> Dict[str, str]:
    """
    Gets the current time for any city worldwide.
    
    This tool retrieves the current date and time in the specified city's timezone
    and returns it in a human-readable format by using a timezone lookup service.
    
    Args:
        city (str): The name of the city to get the current time for
    
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: Current time in the specified city formatted as string
            - error_message: Error description if status is "error"
    """
    try:
        # Use TimeZoneDB API to get timezone for the city
        # This is a free service that doesn't require API key for basic usage
        base_url = "http://api.timezonedb.com/v2.1/get-time-zone"
        params = {
            'key': 'demo',  # Free demo key with limited requests
            'format': 'json',
            'by': 'city',
            'city': city
        }
        
        headers = {
            'User-Agent': 'TimeZone-Tool/1.0'
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'OK':
                # Extract timezone information
                zone_name = data.get('zoneName')
                formatted_time = data.get('formatted')
                
                if zone_name and formatted_time:
                    # Parse and reformat the time
                    try:
                        # Parse the returned time and format it nicely
                        dt = datetime.datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")
                        display_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        
                        return {
                            "status": "success",
                            "report": f"Current time in {city}: {display_time} ({zone_name})"
                        }
                    except ValueError:
                        # If parsing fails, use the original formatted time
                        return {
                            "status": "success",
                            "report": f"Current time in {city}: {formatted_time} ({zone_name})"
                        }
                else:
                    return {
                        "status": "error",
                        "error_message": f"Incomplete timezone data received for city '{city}'"
                    }
            else:
                # API returned an error
                error_msg = data.get('message', 'Unknown error from timezone service')
                return {
                    "status": "error",
                    "error_message": f"Timezone lookup failed for '{city}': {error_msg}"
                }
        else:
            # Fallback: try to use pytz with common timezone patterns
            return _get_time_with_fallback(city)
            
    except requests.exceptions.RequestException:
        # Network error - use fallback
        return _get_time_with_fallback(city)
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get time for {city}: {str(e)}"
        }


def _get_time_with_fallback(city: str) -> Dict[str, str]:
    """Fallback method using pytz for common cities when API fails."""
    try:
        # Common timezone patterns for major cities
        common_timezones = {
            'taipei': 'Asia/Taipei',
            'tokyo': 'Asia/Tokyo',
            'beijing': 'Asia/Shanghai',
            'shanghai': 'Asia/Shanghai',
            'london': 'Europe/London',
            'paris': 'Europe/Paris',
            'new york': 'America/New_York',
            'los angeles': 'America/Los_Angeles',
            'sydney': 'Australia/Sydney'
        }
        
        city_lower = city.lower().strip()
        
        timezone_str = common_timezones.get(city_lower)
        if not timezone_str:
            # Try partial matches
            for key, tz in common_timezones.items():
                if city_lower in key or key in city_lower:
                    timezone_str = tz
                    break
        
        if timezone_str:
            target_tz = pytz.timezone(timezone_str)
            current_time = datetime.datetime.now(target_tz)
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            return {
                "status": "success",
                "report": f"Current time in {city}: {formatted_time}"
            }
        else:
            return {
                "status": "error",
                "error_message": f"Timezone not found for city '{city}'. Please try a major city like Tokyo, London, New York, etc."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get time for {city}: {str(e)}"
        }


def get_temperature(location: str) -> Dict[str, str]:
    """
    Gets the current temperature for a specified location.
    
    This tool uses wttr.in, a free weather service that doesn't require API keys.
    It provides current weather information for any location worldwide.
    
    Args:
        location (str): The name of the city/location to get temperature for
        
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: Temperature information if successful
            - error_message: Error description if status is "error"
    """
    print(f"🔍 Getting temperature for location: {location}")
    try:
        # Use wttr.in - a free weather service
        # Format: ?format=j1 returns JSON with detailed weather info
        base_url = f"https://wttr.in/{location}"
        params = {
            'format': 'j1',  # JSON format with full details
            'u': ''  # Use default units (metric in most places)
        }
        
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': 'curl/7.68.0'
        }
        
        # Make API request
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather information
            current = data['current_condition'][0]
            nearest_area = data['nearest_area'][0]
            
            temp_c = current['temp_C']
            feels_like_c = current['FeelsLikeC']
            humidity = current['humidity']
            description = current['weatherDesc'][0]['value']
            wind_speed = current['windspeedKmph']
            wind_dir = current['winddir16Point']
            
            # Location information
            area_name = nearest_area.get('areaName', [{}])[0].get('value', location)
            country = nearest_area.get('country', [{}])[0].get('value', 'Unknown')
            region = nearest_area.get('region', [{}])[0].get('value', '')
            
            # Build location string
            location_str = area_name
            if region and region != area_name:
                location_str += f", {region}"
            if country and country != 'Unknown':
                location_str += f", {country}"
            
            report = (
                f"Weather in {location_str}:\n"
                f"• Temperature: {temp_c}°C\n"
                f"• Feels like: {feels_like_c}°C\n"
                f"• Humidity: {humidity}%\n"
                f"• Conditions: {description}\n"
                f"• Wind: {wind_speed} km/h {wind_dir}"
            )
            
            print(f"🌡️ Weather report: {report}")
            return {
                "status": "success",
                "report": report
            }
        else:
            return {
                "status": "error",
                "error_message": f"Weather service returned status code {response.status_code}. Location '{location}' might not be found or service is temporarily unavailable."
            }
            
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
    except KeyError as e:
        return {
            "status": "error",
            "error_message": f"Unexpected weather data format. Location '{location}' might not be found."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error getting weather: {str(e)}"
        }


def google_search(query: str, num_results: int = 5) -> Dict[str, str]:
    """
    Performs a Google search and returns the top results.
    
    This tool uses Google Custom Search JSON API to perform searches.
    It returns the top search results with titles, links, and snippets.
    
    Note: This function uses a free Google Custom Search service that may have
    rate limits. For production use, you may need to set up your own API key.
    
    Args:
        query (str): The search query to execute
        num_results (int): Number of results to return (default: 5, max: 10)
        
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: Search results if successful
            - error_message: Error description if status is "error"
    """
    print(f"🔍 Performing Google search for: {query}")
    try:
        # Limit num_results to reasonable bounds
        num_results = max(1, min(10, num_results))
        
        # Use the duckduckgo-search library for reliable search results
        try:
            from duckduckgo_search import DDGS
            
            # Perform web search using the proper DuckDuckGo search library
            with DDGS() as ddgs:
                # Get search results
                search_results = list(ddgs.text(
                    keywords=query,
                    region="wt-wt",
                    safesearch="moderate", 
                    max_results=num_results
                ))
                
                if search_results:
                    # Format the results nicely
                    formatted_results = [f"Search Results for '{query}':\n"]
                    
                    for i, result in enumerate(search_results, 1):
                        title = result.get('title', 'No title')
                        href = result.get('href', '')
                        body = result.get('body', 'No description available')
                        
                        # Truncate body if too long
                        if len(body) > 1024:
                            body = body[:1024] + "..."
                        
                        formatted_results.append(f"{i}. **{title}**")
                        formatted_results.append(f"   {href}")
                        formatted_results.append(f"   {body}")
                        formatted_results.append("")  # Empty line between results
                    
                    report = "\n".join(formatted_results)
                    print(f"🔍 Found {len(search_results)} search results")
                    return {
                        "status": "success",
                        "report": report
                    }
                else:
                    return {
                        "status": "error",
                        "error_message": f"No search results found for '{query}'. Try using different or more general search terms."
                    }
                    
        except ImportError:
            return {
                "status": "error", 
                "error_message": "DuckDuckGo search library is not installed. Please install it with: pip install duckduckgo-search"
            }
        except Exception as search_error:
            print(f"⚠️ DuckDuckGo search failed: {search_error}")
            return {
                "status": "error",
                "error_message": (
                    f"Search failed for '{query}'. This could be due to:\n"
                    "• Network connectivity issues\n"
                    "• Rate limiting from search service\n"
                    "• Invalid search terms\n"
                    f"Error details: {str(search_error)}"
                )
            }
        
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Search request timed out. Please check your internet connection and try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Network error during search: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error during search: {str(e)}"
        }


# Import FunctionTool for Google ADK compatibility
from google.adk.tools import FunctionTool

# Wrap functions with FunctionTool for Google ADK agent usage
current_time_tool = FunctionTool(get_current_time)
temperature_tool = FunctionTool(get_temperature)
google_search_tool = FunctionTool(google_search)

# Tool registry for easy import
AVAILABLE_TOOLS = [
    current_time_tool,
    temperature_tool,
    google_search_tool
]

# Also provide the raw functions for direct testing
RAW_FUNCTIONS = [
    get_current_time,
    get_temperature,
    google_search
]


if __name__ == "__main__":
    """Test the tools directly"""
    print("Testing Google ADK Tools")
    print("=" * 40)
    
    # Test current time tool (raw function)
    print("\n1. Testing get_current_time (raw function):")
    result = get_current_time("Tokyo")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report']}")
    else:
        print(f"Error: {result['error_message']}")
    
    # Test temperature tool (raw function)
    print("\n2. Testing get_temperature (raw function):")
    test_location = "Taipei"
    result = get_temperature(test_location)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report']}")
    else:
        print(f"Error: {result['error_message']}")
    
    # Test Google Search tool (raw function)
    print("\n3. Testing google_search (raw function):")
    test_query = "current USA president"
    result = google_search(test_query, num_results=3)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Report: {result['report'][:1024]}...")  # Show first 200 chars
    else:
        print(f"Error: {result['error_message']}")
    
    # Test FunctionTool wrappers
    print("\n4. Testing FunctionTool wrappers:")
    print(f"✅ current_time_tool: {type(current_time_tool)}")
    print(f"✅ temperature_tool: {type(temperature_tool)}")
    print(f"✅ google_search_tool: {type(google_search_tool)}")
    print(f"✅ AVAILABLE_TOOLS has {len(AVAILABLE_TOOLS)} tools ready for Google ADK agent")