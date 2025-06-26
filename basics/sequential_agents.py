#!/usr/bin/env python3
"""
Sequential Agents for Weather Information Pipeline

This module demonstrates a sequential agent workflow using Google ADK that:
1. Uses a web search agent to find the capital city nearest to a requested location
2. Uses a weather agent to get weather information for that capital city
3. Includes the current time in Taipei at the end

Based on Google ADK Sequential Agents documentation:
https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/
"""

import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import types
from google.adk.models.lite_llm import LiteLlm

# Import our tools
from tools.gadk.tools import google_search_tool, temperature_tool, taipei_time_tool

load_dotenv()


def create_search_agent():
    """Create an agent specialized in finding capital cities using web search"""
    instruction = """You are a Geographic Search Specialist. Your task is to find the capital city of the country nearest to a given location.

When given a location, use the google_search tool to:
1. Search for information about the location and its nearest major capital city
2. Identify which country the location is in, or which country's capital is nearest
3. Find the specific capital city name

Important guidelines:
- If the location is already a capital city, return that city
- If the location is within a country, return that country's capital
- If the location is near borders, find the nearest major capital city
- Focus on finding the CAPITAL CITY specifically, not just major cities
- Be precise about the capital city name

Store your findings using the key "capital_city" in your response.
Format your response as: "The nearest capital city to [location] is [capital_city], [country]."
"""
    
    return Agent(
        name="GeographicSearchAgent",
        model=LiteLlm(model='openai/gpt-4o'),
        instruction=instruction,
        tools=[google_search_tool],
        output_key="capital_city"
    )


def create_weather_agent():
    """Create an agent specialized in getting weather information"""
    instruction = """You are a Weather Information Specialist. Your task is to get current weather information for a specified capital city.

You will receive a capital city location from the previous agent. Use the get_temperature tool to:
1. Get detailed weather information for the capital city
2. Provide comprehensive weather details including temperature, conditions, humidity, and wind
3. Present the information in a clear, user-friendly format

Important guidelines:
- Use the exact capital city name provided by the previous agent
- If the tool returns an error, try variations of the city name
- Provide detailed weather information in an organized format
- Include all available weather metrics

Store your findings using the key "weather_info" in your response.
"""
    
    return Agent(
        name="WeatherInformationAgent", 
        model=LiteLlm(model='openai/gpt-4o'),
        instruction=instruction,
        tools=[temperature_tool],
        output_key="weather_info"
    )


def create_time_agent():
    """Create an agent specialized in adding Taipei time information"""
    instruction = """You are a Time Information Specialist. Your task is to get the current time in Taipei and compile a final weather report.

You will receive weather information from the previous agent. Use the get_taipei_time tool to:
1. Get the current time in Taipei, Taiwan
2. Combine all the information into a comprehensive final report
3. Present everything in a well-organized, user-friendly format

Important guidelines:
- Always include the Taipei time at the end of your response
- Organize the information logically: location → weather → time
- Make the final response comprehensive and easy to read
- Use clear formatting and structure

Store your final report using the key "final_report" in your response.
"""
    
    return Agent(
        name="TimeInformationAgent",
        model=LiteLlm(model='openai/gpt-4o'), 
        instruction=instruction,
        tools=[taipei_time_tool],
        output_key="final_report"
    )


def create_weather_pipeline():
    """Create the sequential agent pipeline for weather information"""
    
    # Create individual specialized agents
    search_agent = create_search_agent()
    weather_agent = create_weather_agent()
    time_agent = create_time_agent()
    
    # Create the sequential workflow
    pipeline = SequentialAgent(
        sub_agents=[search_agent, weather_agent, time_agent],
        name="WeatherInformationPipeline",
        description="A sequential workflow that finds the nearest capital city, gets its weather, and includes Taipei time"
    )
    
    return pipeline


async def run_weather_pipeline(location: str):
    """
    Run the weather information pipeline for a given location
    
    Args:
        location (str): The location to get weather information for
        
    Returns:
        str: The final weather report including Taipei time
    """
    # Create the pipeline
    pipeline = create_weather_pipeline()
    
    # Set up session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="WeatherInformationPipeline",
        agent=pipeline,
        session_service=session_service
    )
    
    # Create a session
    await session_service.create_session(
        user_id="weather_user",
        session_id="weather_session", 
        app_name="WeatherInformationPipeline"
    )
    
    # Create the user message
    user_query = f"I want to know the weather for {location}. Please find the nearest capital city and get its weather information."
    message = types.Content(role="user", parts=[{"text": user_query}])
    
    # Run the pipeline
    print(f"🌍 Starting weather information pipeline for: {location}")
    print("=" * 60)
    
    try:
        response_generator = runner.run(
            user_id="weather_user",
            session_id="weather_session",
            new_message=message
        )
        
        final_response = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
        
        return final_response
        
    except Exception as e:
        error_msg = f"Error running weather pipeline: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


async def main():
    """Main function to demonstrate the sequential weather agents"""
    print("🤖 Sequential Weather Information Pipeline")
    print("==========================================")
    print("This pipeline will:")
    print("1. 🔍 Find the nearest capital city to your location")
    print("2. 🌤️  Get weather information for that capital city") 
    print("3. 🕐 Include the current time in Taipei")
    print()
    
    # Example locations to test
    test_locations = [
        "Tokyo, Japan",
        "San Francisco, USA", 
        "London, UK"
    ]
    
    for location in test_locations:
        print(f"\n🌍 Testing location: {location}")
        print("-" * 50)
        
        result = await run_weather_pipeline(location)
        print("📋 Final Result:")
        print(result)
        print("\n" + "=" * 60)


def interactive_mode():
    """Interactive mode for testing the weather pipeline"""
    print("🤖 Interactive Weather Information Pipeline")
    print("==========================================")
    print("Enter a location to get weather information for its nearest capital city.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            location = input("🌍 Enter location: ").strip()
            
            if location.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not location:
                print("❌ Please enter a valid location.")
                continue
            
            print(f"\n🔄 Processing weather information for: {location}")
            result = asyncio.run(run_weather_pipeline(location))
            print("\n📋 Final Result:")
            print(result)
            print("\n" + "=" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sequential Weather Information Pipeline")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--location", type=str, 
                       help="Specific location to get weather for")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.location:
        result = asyncio.run(run_weather_pipeline(args.location))
        print("\n📋 Final Result:")
        print(result)
    else:
        # Run demo with example locations
        asyncio.run(main())