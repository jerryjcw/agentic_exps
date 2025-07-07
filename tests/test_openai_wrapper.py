#!/usr/bin/env python3
"""
Unit tests for OpenAI LiteLLM Wrapper

This module contains comprehensive tests for the OpenAI to LiteLLM wrapper functionality,
equivalent to the original model_wrapper_test.py file.
"""

import os
import sys
import unittest
import asyncio
from dotenv import load_dotenv

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wrapper_dir = os.path.join(project_root, 'wrapper')
core_dir = os.path.join(project_root, 'core')
sys.path.extend([wrapper_dir, core_dir, project_root])

try:
    from google.adk.agents import Agent, SequentialAgent
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import types
    GOOGLE_ADK_AVAILABLE = True
except ImportError as e:
    GOOGLE_ADK_AVAILABLE = False
    print(f"Warning: Google ADK not available: {e}")

try:
    from openai_litellm_wrapper import create_openai_litellm_wrapper
    from gpt_caller import get_openai_client
    OPENAI_WRAPPER_AVAILABLE = True
except ImportError as e:
    OPENAI_WRAPPER_AVAILABLE = False
    print(f"Warning: OpenAI wrapper not available: {e}")

try:
    from tools.gadk.tools import google_search_tool, temperature_tool, current_time_tool
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    print("Warning: Tools not available")

load_dotenv()


class BaseOpenAIWrapperTest(unittest.TestCase):
    """Base class for OpenAI wrapper tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not GOOGLE_ADK_AVAILABLE:
            self.skipTest("Google ADK not available")
        if not OPENAI_WRAPPER_AVAILABLE:
            self.skipTest("OpenAI wrapper not available")
        
        # Check for API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            try:
                from gpt_caller import get_api_key
                api_key_path = os.path.join(project_root, 'config', 'apikey')
                self.api_key = get_api_key(file_path=api_key_path)
                os.environ["OPENAI_API_KEY"] = self.api_key
            except Exception:
                self.skipTest("No API key available for OpenAI wrapper tests")
    
    def create_openai_wrapper_model(self, api_key_file=None, model="gpt-4o"):
        """Create an OpenAI LiteLLM wrapper model using existing OpenAI client setup."""
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


class TestOpenAIWrapperCreation(BaseOpenAIWrapperTest):
    """Test OpenAI wrapper creation functionality."""
    
    def test_create_openai_wrapper_model(self):
        """Test creating the OpenAI wrapper model."""
        model = self.create_openai_wrapper_model()
        
        # Check that we got a valid wrapper
        self.assertIsNotNone(model)
        self.assertEqual(model.model, "gpt-4o")
        self.assertEqual(model.temperature, 0.7)
        self.assertEqual(model.max_tokens, 1000)
    
    def test_create_with_custom_parameters(self):
        """Test creating wrapper with custom parameters."""
        model = self.create_openai_wrapper_model(model="gpt-3.5-turbo")
        
        self.assertEqual(model.model, "gpt-3.5-turbo")
        self.assertEqual(model.temperature, 0.7)
        self.assertEqual(model.max_tokens, 1000)


class TestSimpleAgentWithOpenAIWrapper(BaseOpenAIWrapperTest):
    """Test simple agent functionality with OpenAI wrapper."""
    
    def create_simple_agent_with_wrapper(self):
        """Create a simple agent using the OpenAI wrapper."""
        # Create the wrapped model
        model = self.create_openai_wrapper_model()
        
        instruction = """You are a helpful assistant. Answer questions clearly and concisely.
        If you don't know something, say so honestly."""
        
        # Create agent with wrapper model
        agent = Agent(
            name="OpenAIWrapperAgent",
            model=model,
            instruction=instruction
        )
        
        return agent
    
    async def run_simple_agent_test(self):
        """Run the simple agent test."""
        # Create agent
        agent = self.create_simple_agent_with_wrapper()
        
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
        message = types.Content(role="user", parts=[types.Part(text=test_query)])
        
        # Run the query
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
        
        return response_text.strip()
    
    def test_simple_agent(self):
        """Test the simple agent with OpenAI wrapper."""
        async def _test():
            response = await self.run_simple_agent_test()
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertIn("Paris", response)
        
        asyncio.run(_test())


@unittest.skipUnless(TOOLS_AVAILABLE, "Tools not available")
class TestWeatherAgentWithOpenAIWrapper(BaseOpenAIWrapperTest):
    """Test weather agent functionality with OpenAI wrapper."""
    
    def create_weather_agent_with_wrapper(self):
        """Create a weather agent using the OpenAI wrapper."""
        # Create the wrapped model
        model = self.create_openai_wrapper_model()
        
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
    
    async def run_weather_agent_test(self):
        """Run the weather agent test."""
        # Create agent
        agent = self.create_weather_agent_with_wrapper()
        
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
        message = types.Content(role="user", parts=[types.Part(text=test_query)])
        
        # Run the query
        response_generator = runner.run(
            user_id="weather_user",
            session_id="weather_session",
            new_message=message
        )
        
        response_text = ""
        tool_calls = []
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                        elif hasattr(part, 'function_call') and part.function_call:
                            tool_calls.append(part.function_call.name)
        
        return response_text.strip(), tool_calls
    
    def test_weather_agent(self):
        """Test the weather agent with OpenAI wrapper."""
        async def _test():
            response, tool_calls = await self.run_weather_agent_test()
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            # Should call temperature tool for weather
            self.assertIn("get_temperature", tool_calls)
        
        asyncio.run(_test())


@unittest.skipUnless(TOOLS_AVAILABLE, "Tools not available")
class TestSequentialAgentsWithOpenAIWrapper(BaseOpenAIWrapperTest):
    """Test sequential agents functionality with OpenAI wrapper."""
    
    def create_sequential_agents_with_wrapper(self):
        """Create a sequential agent pipeline using the OpenAI wrapper."""
        # Create agents with tools
        search_model = self.create_openai_wrapper_model()
        weather_model = self.create_openai_wrapper_model()
        time_model = self.create_openai_wrapper_model()
        
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
            instruction="Add current time for any city to the weather report.",
            tools=[current_time_tool],
            output_key="final_report"
        )
        
        # Create sequential pipeline
        pipeline = SequentialAgent(
            sub_agents=[search_agent, weather_agent, time_agent],
            name="WeatherPipelineWithWrapper",
            description="Weather information pipeline using OpenAI wrapper"
        )
        
        return pipeline
    
    async def run_sequential_agents_test(self):
        """Run the sequential agents test."""
        # Create pipeline
        pipeline = self.create_sequential_agents_with_wrapper()
        
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
        message = types.Content(role="user", parts=[types.Part(text=test_query)])
        
        # Run the query
        response_generator = runner.run(
            user_id="sequential_user",
            session_id="sequential_session",
            new_message=message
        )
        
        response_text = ""
        tool_calls = []
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                        elif hasattr(part, 'function_call') and part.function_call:
                            tool_calls.append(part.function_call.name)
        
        return response_text.strip(), tool_calls
    
    def test_sequential_agents(self):
        """Test sequential agents with OpenAI wrapper."""
        async def _test():
            response, tool_calls = await self.run_sequential_agents_test()
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            # Should use multiple tools in sequence
            self.assertGreater(len(tool_calls), 0)
        
        asyncio.run(_test())


if __name__ == '__main__':
    # Set up test environment
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Run tests
    unittest.main(verbosity=2)