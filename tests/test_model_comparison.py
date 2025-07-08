#!/usr/bin/env python3
"""
Model Comparison Tests

This module contains tests that compare the behavior of LiteLlm vs LangChain wrapper
to ensure they provide consistent responses and behavior.
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
    from google.adk.models.lite_llm import LiteLlm
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
    from tools.gadk.registry import get_all_tools
    AVAILABLE_TOOLS = get_all_tools()
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False

try:
    from gpt_caller import get_api_key
except ImportError:
    def get_api_key(file_path=None):
        return os.getenv("OPENAI_API_KEY")

load_dotenv()


class BaseComparisonTest(unittest.TestCase):
    """Base class for comparison tests."""
    
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
                self.skipTest("No API key available for comparison tests")
    
    def create_litellm_agent(self, tools=None):
        """Create an agent using LiteLlm."""
        instruction = "You are a helpful assistant. Answer questions clearly and concisely."
        if tools:
            instruction += " Use the available tools when appropriate."
        
        agent = Agent(
            name="LiteLLM_Agent",
            model=LiteLlm(model='openai/gpt-4o'),
            instruction=instruction,
            tools=tools or []
        )
        return agent
    
    def create_langchain_agent(self, tools=None):
        """Create an agent using LangChain wrapper."""
        langchain_model = init_chat_model("openai:gpt-4o")
        model = create_langchain_litellm_wrapper(
            langchain_model=langchain_model,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=500
        )
        
        instruction = "You are a helpful assistant. Answer questions clearly and concisely."
        if tools:
            instruction += " Use the available tools when appropriate."
        
        agent = Agent(
            name="LangChain_Agent",
            model=model,
            instruction=instruction,
            tools=tools or []
        )
        return agent
    
    async def _test_agent_with_query(self, agent, query, agent_name):
        """Test an agent with a single query and return response details."""
        session_service = InMemorySessionService()
        runner = Runner(
            app_name=f"ComparisonTest_{agent_name}",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        await session_service.create_session(
            user_id=f"test_user_{agent_name.lower()}",
            session_id=f"test_session_{agent_name.lower()}",
            app_name=f"ComparisonTest_{agent_name}"
        )
        
        try:
            # Create message
            message = types.Content(role="user", parts=[types.Part(text=query)])
            
            # Run the agent
            response_generator = runner.run(
                user_id=f"test_user_{agent_name.lower()}",
                session_id=f"test_session_{agent_name.lower()}",
                new_message=message
            )
            
            # Collect response
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
            
            return {
                'success': True,
                'response': response_text.strip(),
                'tool_calls': tool_calls,
                'length': len(response_text.strip())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': "",
                'tool_calls': [],
                'length': 0
            }


class TestBasicResponseConsistency(BaseComparisonTest):
    """Test basic response consistency between models."""
    
    def test_simple_factual_questions(self):
        """Test simple factual questions."""
        async def _test():
            queries = [
                "What is the capital of France?",
                "What is 15 * 23?",
                "Who wrote Romeo and Juliet?"
            ]
            
            litellm_agent = self.create_litellm_agent()
            langchain_agent = self.create_langchain_agent()
            
            for query in queries:
                with self.subTest(query=query):
                    # Test both agents
                    lite_result = await self._test_agent_with_query(litellm_agent, query, "LiteLLM")
                    lang_result = await self._test_agent_with_query(langchain_agent, query, "LangChain")
                    
                    # Both should succeed
                    self.assertTrue(lite_result['success'], f"LiteLLM failed: {lite_result.get('error', '')}")
                    self.assertTrue(lang_result['success'], f"LangChain failed: {lang_result.get('error', '')}")
                    
                    # Both should have non-empty responses
                    self.assertGreater(lite_result['length'], 0)
                    self.assertGreater(lang_result['length'], 0)
                    
                    # Tool usage should be identical (none for these queries)
                    self.assertEqual(lite_result['tool_calls'], lang_result['tool_calls'])
        
        asyncio.run(_test())
    
    def test_creative_responses(self):
        """Test creative responses (these may vary more)."""
        async def _test():
            queries = [
                "Write a short poem about coding.",
                "Tell me a joke about programming."
            ]
            
            litellm_agent = self.create_litellm_agent()
            langchain_agent = self.create_langchain_agent()
            
            for query in queries:
                with self.subTest(query=query):
                    lite_result = await self._test_agent_with_query(litellm_agent, query, "LiteLLM")
                    lang_result = await self._test_agent_with_query(langchain_agent, query, "LangChain")
                    
                    # Both should succeed
                    self.assertTrue(lite_result['success'])
                    self.assertTrue(lang_result['success'])
                    
                    # Both should have reasonable length responses
                    self.assertGreater(lite_result['length'], 10)
                    self.assertGreater(lang_result['length'], 10)
        
        asyncio.run(_test())


class TestConversationConsistency(BaseComparisonTest):
    """Test conversation consistency between models."""
    
    async def run_conversation(self, agent, queries, agent_name):
        """Run a multi-turn conversation and return all responses."""
        session_service = InMemorySessionService()
        runner = Runner(
            app_name=f"ConversationTest_{agent_name}",
            agent=agent,
            session_service=session_service
        )
        
        await session_service.create_session(
            user_id=f"conv_user_{agent_name.lower()}",
            session_id=f"conv_session_{agent_name.lower()}",
            app_name=f"ConversationTest_{agent_name}"
        )
        
        responses = []
        
        for query in queries:
            message = types.Content(role="user", parts=[types.Part(text=query)])
            
            response_generator = runner.run(
                user_id=f"conv_user_{agent_name.lower()}",
                session_id=f"conv_session_{agent_name.lower()}",
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
    
    def test_memory_consistency(self):
        """Test that both models handle conversation memory consistently."""
        async def _test():
            conversation_queries = [
                "Hello, my name is Alice.",
                "What is my name?",
                "What is 10 + 5?",
                "What was the previous calculation result?"
            ]
            
            litellm_agent = self.create_litellm_agent()
            langchain_agent = self.create_langchain_agent()
            
            # Run conversations
            lite_responses = await self.run_conversation(litellm_agent, conversation_queries, "LiteLLM")
            lang_responses = await self.run_conversation(langchain_agent, conversation_queries, "LangChain")
            
            self.assertEqual(len(lite_responses), len(conversation_queries))
            self.assertEqual(len(lang_responses), len(conversation_queries))
            
            # Check memory tests
            memory_tests = [
                (1, "alice"),  # Should remember Alice
                (3, "15")      # Should remember calculation result
            ]
            
            for response_index, expected_content in memory_tests:
                with self.subTest(test=f"memory_{response_index}_{expected_content}"):
                    lite_resp = lite_responses[response_index].lower()
                    lang_resp = lang_responses[response_index].lower()
                    
                    lite_has_content = expected_content.lower() in lite_resp
                    lang_has_content = expected_content.lower() in lang_resp
                    
                    # Both should remember the information
                    self.assertTrue(lite_has_content, f"LiteLLM didn't remember {expected_content}")
                    self.assertTrue(lang_has_content, f"LangChain didn't remember {expected_content}")
        
        asyncio.run(_test())


@unittest.skipUnless(TOOLS_AVAILABLE, "Tools not available")
class TestToolUsageConsistency(BaseComparisonTest):
    """Test tool usage consistency between models."""
    
    def test_tool_calling_behavior(self):
        """Test that both models call tools consistently."""
        async def _test():
            tool_queries = [
                ("What time is it in Taipei right now?", "get_current_time"),
                ("What's the weather in Tokyo?", "get_temperature")
            ]
            
            litellm_agent = self.create_litellm_agent(AVAILABLE_TOOLS)
            langchain_agent = self.create_langchain_agent(AVAILABLE_TOOLS)
            
            for query, expected_tool in tool_queries:
                with self.subTest(query=query):
                    lite_result = await self._test_agent_with_query(litellm_agent, query, "LiteLLM")
                    lang_result = await self._test_agent_with_query(langchain_agent, query, "LangChain")
                    
                    # Both should succeed
                    self.assertTrue(lite_result['success'])
                    self.assertTrue(lang_result['success'])
                    
                    # Both should call the expected tool
                    self.assertIn(expected_tool, lite_result['tool_calls'], 
                                f"LiteLLM didn't call {expected_tool}")
                    self.assertIn(expected_tool, lang_result['tool_calls'], 
                                f"LangChain didn't call {expected_tool}")
        
        asyncio.run(_test())


class TestResponseQuality(BaseComparisonTest):
    """Test response quality metrics."""
    
    def test_response_length_consistency(self):
        """Test that response lengths are reasonably consistent."""
        async def _test():
            queries = [
                "Explain quantum computing in simple terms.",
                "What are the benefits of renewable energy?"
            ]
            
            litellm_agent = self.create_litellm_agent()
            langchain_agent = self.create_langchain_agent()
            
            for query in queries:
                with self.subTest(query=query):
                    lite_result = await self._test_agent_with_query(litellm_agent, query, "LiteLLM")
                    lang_result = await self._test_agent_with_query(langchain_agent, query, "LangChain")
                    
                    # Both should succeed
                    self.assertTrue(lite_result['success'])
                    self.assertTrue(lang_result['success'])
                    
                    # Calculate length difference ratio
                    max_length = max(lite_result['length'], lang_result['length'])
                    min_length = min(lite_result['length'], lang_result['length'])
                    
                    if max_length > 0:
                        length_ratio = min_length / max_length
                        # Responses should be within 50% of each other in length
                        self.assertGreater(length_ratio, 0.5, 
                                         f"Response lengths too different: {lite_result['length']} vs {lang_result['length']}")
        
        asyncio.run(_test())


if __name__ == '__main__':
    # Set up test environment
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Run tests
    unittest.main(verbosity=2)