#!/usr/bin/env python3
"""
Google ADK Compatible Tools

This module provides tools that can be used with Google ADK agents:
1. get_taipei_time - Gets current time in Taipei, Taiwan
2. get_temperature - Gets current temperature for a given location
"""

import datetime
import pytz
import requests
import os
from typing import Dict


def get_taipei_time() -> Dict[str, str]:
    """
    Gets the current time in Taipei, Taiwan.
    
    This tool retrieves the current date and time in Taipei timezone
    and returns it in a human-readable format.
    
    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - report: Current time in Taipei formatted as string
            - error_message: Error description if status is "error"
    """
    try:
        # Get current time in Taipei timezone
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.datetime.now(taipei_tz)
        
        # Format the time nicely
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return {
            "status": "success",
            "report": f"Current time in Taipei, Taiwan: {formatted_time}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get Taipei time: {str(e)}"
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


# Import FunctionTool for Google ADK compatibility
from google.adk.tools import FunctionTool

# Wrap functions with FunctionTool for Google ADK agent usage
taipei_time_tool = FunctionTool(get_taipei_time)
temperature_tool = FunctionTool(get_temperature)

# Tool registry for easy import
AVAILABLE_TOOLS = [
    taipei_time_tool,
    temperature_tool
]

# Also provide the raw functions for direct testing
RAW_FUNCTIONS = [
    get_taipei_time,
    get_temperature
]


if __name__ == "__main__":
    """Test the tools directly"""
    print("Testing Google ADK Tools")
    print("=" * 40)
    
    # Test Taipei time tool (raw function)
    print("\n1. Testing get_taipei_time (raw function):")
    result = get_taipei_time()
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
    
    # Test FunctionTool wrappers
    print("\n3. Testing FunctionTool wrappers:")
    print(f"✅ taipei_time_tool: {type(taipei_time_tool)}")
    print(f"✅ temperature_tool: {type(temperature_tool)}")
    print(f"✅ AVAILABLE_TOOLS has {len(AVAILABLE_TOOLS)} tools ready for Google ADK agent")