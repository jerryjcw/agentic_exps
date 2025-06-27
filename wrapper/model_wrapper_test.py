#!/usr/bin/env python3
"""
Example usage of OpenAI LiteLLM Wrapper with Google ADK Agents

This example demonstrates how to use the OpenAI LiteLLM wrapper
with Google ADK agents, replacing the standard LiteLLM model.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import types

# Import our wrapper and existing OpenAI setup
from openai_litellm_wrapper import create_openai_litellm_wrapper
from gpt_caller import get_openai_client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from tools.gadk.tools import google_search_tool, temperature_tool, taipei_time_tool

def create_openai_wrapper_model(api_key_file: str = None, model: str = "gpt-4o"):
    """
    Create an OpenAI LiteLLM wrapper model using existing OpenAI client setup.
    
    Args:
        api_key_file: Path to API key file (optional, uses env var if None)
        model: Model name to use (default: gpt-4o)
        
    Returns:
        OpenAILiteLLMWrapper instance
    """
    # Use existing OpenAI client setup from gpt_caller.py
    openai_client = get_openai_client(api_key_file)
    
    # Create the wrapper
    wrapper_model = create_openai_litellm_wrapper(
        openai_client=openai_client,
        model=model,
        temperature=0.7,
        max_tokens=1000
    )
    
    return wrapper_model


def create_simple_agent_with_wrapper():
    """Create a simple agent using the OpenAI wrapper"""
    
    # Create the wrapped model
    model = create_openai_wrapper_model()
    
    instruction = """You are a helpful assistant. Answer questions clearly and concisely.
    If you don't know something, say so honestly."""
    
    # Create agent with wrapper model
    agent = Agent(
        name="OpenAIWrapperAgent",
        model=model,
        instruction=instruction,
        tools=[google_search_tool]
    )
    
    return agent


def create_weather_agent_with_wrapper():
    """Create a weather agent using the OpenAI wrapper (if tools are available)"""
    
    # Create the wrapped model
    model = create_openai_wrapper_model()
    
    instruction = """You are a weather information specialist. Use the available tools to:
    1. Search for weather information about requested locations
    2. Get current temperature and weather conditions
    3. Provide comprehensive weather reports
    
    Be helpful and accurate in your responses."""
    
    # Create agent with wrapper model and weather tools
    agent = Agent(
        name="WeatherAgentWithWrapper",
        model=model,
        instruction=instruction,
        tools=[google_search_tool, temperature_tool]
    )
    
    return agent


def create_sequential_agents_with_wrapper():
    """Create a sequential agent pipeline using the OpenAI wrapper"""
    
    # Create agents with tools
    search_model = create_openai_wrapper_model()
    weather_model = create_openai_wrapper_model()
    time_model = create_openai_wrapper_model()
    
    # Search agent
    search_agent = Agent(
        name="SearchAgent",
        model=search_model,
        instruction="Find the nearest capital city to the given location using web search.",
        tools=[google_search_tool],
        output_key="capital_city"
    )
    
    # Weather agent
    weather_agent = Agent(
        name="WeatherAgent", 
        model=weather_model,
        instruction="Get weather information for the capital city found by the previous agent.",
        tools=[temperature_tool],
        output_key="weather_info"
    )
    
    # Time agent
    time_agent = Agent(
        name="TimeAgent",
        model=time_model,
        instruction="Add current Taipei time to the weather report.",
        tools=[taipei_time_tool],
        output_key="final_report"
    )
    
    # Create sequential pipeline
    pipeline = SequentialAgent(
        sub_agents=[search_agent, weather_agent, time_agent],
        name="WeatherPipelineWithWrapper",
        description="Weather information pipeline using OpenAI wrapper"
    )
    
    return pipeline


async def test_simple_agent():
    """Test the simple agent with OpenAI wrapper"""
    print("🤖 Testing Simple Agent with OpenAI Wrapper")
    print("=" * 50)
    
    # Create agent
    agent = create_simple_agent_with_wrapper()
    
    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="OpenAIWrapperTest",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    await session_service.create_session(
        user_id="test_user",
        session_id="test_session",
        app_name="OpenAIWrapperTest"
    )
    
    # Test query
    test_query = "What is the capital of France?"
    message = types.Content(role="user", parts=[{"text": test_query}])
    
    print(f"Query: {test_query}")
    print("Response:", end=" ")
    
    try:
        response_generator = runner.run(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        )
        
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
        
        print(response_text)
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def test_weather_agent():
    """Test the weather agent with OpenAI wrapper"""
    print("\n🌤️ Testing Weather Agent with OpenAI Wrapper")
    print("=" * 50)
    
    # Create agent
    agent = create_weather_agent_with_wrapper()
    
    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="WeatherAgentTest",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    await session_service.create_session(
        user_id="weather_user",
        session_id="weather_session",
        app_name="WeatherAgentTest"
    )
    
    # Test query
    test_query = "What's the weather like in Tokyo?"
    message = types.Content(role="user", parts=[{"text": test_query}])
    
    print(f"Query: {test_query}")
    print("Response:")
    
    try:
        response_generator = runner.run(
            user_id="weather_user",
            session_id="weather_session",
            new_message=message
        )
        
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
        
        print(response_text)
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def test_sequential_agents():
    """Test sequential agents with OpenAI wrapper"""
    print("\n🔄 Testing Sequential Agents with OpenAI Wrapper")
    print("=" * 50)
    
    # Create pipeline
    pipeline = create_sequential_agents_with_wrapper()
    
    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="SequentialAgentTest",
        agent=pipeline,
        session_service=session_service
    )
    
    # Create session
    await session_service.create_session(
        user_id="sequential_user",
        session_id="sequential_session",
        app_name="SequentialAgentTest"
    )
    
    # Test query
    test_query = "Tell me about the weather in London"
    
    message = types.Content(role="user", parts=[{"text": test_query}])
    
    print(f"Query: {test_query}")
    print("Response:")
    
    try:
        response_generator = runner.run(
            user_id="sequential_user",
            session_id="sequential_session",
            new_message=message
        )
        
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
        
        print(response_text)
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 OpenAI LiteLLM Wrapper Integration Tests")
    print("=" * 60)
    
    # Test simple agent
    success1 = await test_simple_agent()
    
    # Test weather agent
    success2 = await test_weather_agent()
    
    # Test sequential agents
    success3 = await test_sequential_agents()
    
    print("\n📊 Test Results:")
    print(f"Simple Agent: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Weather Agent: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Sequential Agents: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 All tests passed! The OpenAI wrapper is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")