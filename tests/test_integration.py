#!/usr/bin/env python3
"""
Integration tests for LangChain LiteLLM Wrapper with Google ADK

This module contains integration tests that verify the LangChain wrapper works
correctly with Google ADK agents and tools.
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
    from google.adk.agents import Agent
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import types
    GOOGLE_ADK_AVAILABLE = True
except ImportError as e:
    GOOGLE_ADK_AVAILABLE = False
    print(f"Warning: Google ADK not available: {e}")

try:
    from langchain_litellm_wrapper import create_langchain_litellm_wrapper
    from langchain.chat_models import init_chat_model
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"Warning: LangChain not available: {e}")

try:
    from tools.gadk.registry import registry
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    print("Warning: Tools not available")

try:
    from gpt_caller import get_api_key
except ImportError:
    def get_api_key(file_path=None):
        return os.getenv("OPENAI_API_KEY")

load_dotenv()


class BaseIntegrationTest(unittest.TestCase):
    """Base class for integration tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not GOOGLE_ADK_AVAILABLE:
            self.skipTest("Google ADK not available")
        if not LANGCHAIN_AVAILABLE:
            self.skipTest("LangChain not available")
        
        # Check for API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            try:
                api_key_path = os.path.join(project_root, 'config', 'apikey')
                self.api_key = get_api_key(file_path=api_key_path)
                os.environ["OPENAI_API_KEY"] = self.api_key
            except Exception:
                self.skipTest("No API key available for integration tests")


class TestSimpleAgentIntegration(BaseIntegrationTest):
    """Test simple agent functionality with LangChain wrapper."""
    
    def create_simple_agent(self):
        """Create a simple agent using the LangChain wrapper."""
        # Create the wrapped model
        langchain_model = init_chat_model("openai:gpt-4o")
        model = create_langchain_litellm_wrapper(
            langchain_model=langchain_model,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=200
        )
        
        instruction = "You are a helpful assistant. Answer questions clearly and concisely."
        
        agent = Agent(
            name="TestLangChainAgent",
            model=model,
            instruction=instruction
        )
        
        return agent
    
    async def run_agent_query(self, agent, query):
        """Run a single query against an agent and return the response."""
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="IntegrationTest",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        await session_service.create_session(
            user_id="test_user",
            session_id="test_session",
            app_name="IntegrationTest"
        )
        
        # Create message
        message = types.Content(role="user", parts=[types.Part(text=query)])
        
        # Run the agent
        response_generator = runner.run(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        )
        
        # Collect response
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
        
        return response_text.strip()
    
    def test_simple_query(self):
        """Test a simple query to the agent."""
        async def _test():
            agent = self.create_simple_agent()
            response = await self.run_agent_query(agent, "What is the capital of France?")
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertIn("Paris", response)
        
        asyncio.run(_test())
    
    def test_math_query(self):
        """Test a mathematical query."""
        async def _test():
            agent = self.create_simple_agent()
            response = await self.run_agent_query(agent, "What is 15 * 23?")
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertIn("345", response)
        
        asyncio.run(_test())


class TestConversationMemory(BaseIntegrationTest):
    """Test conversation memory functionality."""
    
    async def run_conversation(self, agent, queries):
        """Run a multi-turn conversation with an agent."""
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="ConversationTest",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        await session_service.create_session(
            user_id="conv_user",
            session_id="conv_session",
            app_name="ConversationTest"
        )
        
        responses = []
        for query in queries:
            message = types.Content(role="user", parts=[types.Part(text=query)])
            
            response_generator = runner.run(
                user_id="conv_user",
                session_id="conv_session",
                new_message=message
            )
            
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
            
            responses.append(response_text.strip())
        
        return responses
    
    def test_name_memory(self):
        """Test that the agent remembers the user's name."""
        async def _test():
            # Create agent
            langchain_model = init_chat_model("openai:gpt-4o")
            model = create_langchain_litellm_wrapper(langchain_model=langchain_model)
            
            agent = Agent(
                name="MemoryTestAgent",
                model=model,
                instruction="You are a helpful assistant. Remember information from the conversation."
            )
            
            # Run conversation
            queries = [
                "Hello, my name is Alice.",
                "What is my name?"
            ]
            
            responses = await self.run_conversation(agent, queries)
            
            self.assertEqual(len(responses), 2)
            self.assertGreater(len(responses[0]), 0)
            self.assertGreater(len(responses[1]), 0)
            
            # Check that the second response mentions Alice
            self.assertIn("Alice", responses[1])
        
        asyncio.run(_test())


@unittest.skipUnless(TOOLS_AVAILABLE, "Tools not available")
class TestToolIntegration(BaseIntegrationTest):
    """Test tool integration with LangChain wrapper."""
    
    def create_agent_with_tools(self):
        """Create an agent with tools using the LangChain wrapper."""
        langchain_model = init_chat_model("openai:gpt-4o")
        model = create_langchain_litellm_wrapper(
            langchain_model=langchain_model,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=500
        )
        
        instruction = """You are a helpful assistant with access to various tools.
        
        Available tools:
        1. google_search_tool - Search the web for information
        2. temperature_tool - Get current weather and temperature for any location
        3. current_time_tool - Get current time for any city worldwide
        
        When a user asks for information that requires these tools, use them appropriately."""
        
        agent = Agent(
            name="ToolTestAgent",
            model=model,
            instruction=instruction,
            tools=[registry.google_search_tool, registry.get_temperature_tool, registry.get_current_time_tool]
        )
        
        return agent
    
    async def run_agent_with_tool_detection(self, agent, query):
        """Run agent query and detect tool usage."""
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="ToolTest",
            agent=agent,
            session_service=session_service
        )
        
        await session_service.create_session(
            user_id="tool_user",
            session_id="tool_session",
            app_name="ToolTest"
        )
        
        message = types.Content(role="user", parts=[types.Part(text=query)])
        
        response_generator = runner.run(
            user_id="tool_user",
            session_id="tool_session",
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
    
    def test_current_time_tool(self):
        """Test current time tool usage."""
        async def _test():
            agent = self.create_agent_with_tools()
            response, tool_calls = await self.run_agent_with_tool_detection(
                agent, "What time is it in Taipei right now?"
            )
            
            self.assertGreater(len(response), 0)
            self.assertIn("get_current_time", tool_calls)
            self.assertIn("Taipei", response)
        
        asyncio.run(_test())
    
    def test_temperature_tool(self):
        """Test temperature tool usage."""
        async def _test():
            agent = self.create_agent_with_tools()
            response, tool_calls = await self.run_agent_with_tool_detection(
                agent, "What's the weather like in Tokyo?"
            )
            
            self.assertGreater(len(response), 0)
            self.assertIn("get_temperature", tool_calls)
            # Response should contain weather information
            self.assertTrue(
                any(word in response.lower() for word in ["temperature", "weather", "tokyo"])
            )
        
        asyncio.run(_test())


if __name__ == '__main__':
    # Set up test environment
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Run tests
    unittest.main(verbosity=2)