#!/usr/bin/env python3
"""
Unit tests for LangChain LiteLLM Wrapper

This module contains unit tests for the LangChain to LiteLLM wrapper functionality.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wrapper_dir = os.path.join(project_root, 'wrapper')
core_dir = os.path.join(project_root, 'core')
sys.path.extend([wrapper_dir, core_dir])

try:
    from langchain_litellm_wrapper import create_langchain_litellm_wrapper, LangChainLiteLLMWrapper
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"Warning: LangChain not available: {e}")

try:
    from gpt_caller import get_api_key
except ImportError:
    def get_api_key(file_path=None):
        return os.getenv("OPENAI_API_KEY")


class TestLangChainWrapperCreation(unittest.TestCase):
    """Test wrapper creation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not LANGCHAIN_AVAILABLE:
            self.skipTest("LangChain not available")
    
    def test_wrapper_creation_without_api_key(self):
        """Test wrapper creation without API key (mock test)."""
        from langchain_openai import ChatOpenAI
        
        # Create a mock LangChain model
        mock_model = ChatOpenAI(model="gpt-4o", api_key="test-key")
        
        # Create the wrapper
        wrapper = create_langchain_litellm_wrapper(
            langchain_model=mock_model,
            model="gpt-4o"
        )
        
        self.assertIsInstance(wrapper, LangChainLiteLLMWrapper)
        self.assertEqual(wrapper.model, "gpt-4o")
        self.assertEqual(wrapper.temperature, 0.7)
        self.assertEqual(wrapper.max_tokens, 1000)
    
    def test_wrapper_custom_parameters(self):
        """Test wrapper creation with custom parameters."""
        from langchain_openai import ChatOpenAI
        
        mock_model = ChatOpenAI(model="gpt-3.5-turbo", api_key="test-key")
        
        wrapper = create_langchain_litellm_wrapper(
            langchain_model=mock_model,
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=500
        )
        
        self.assertEqual(wrapper.model, "gpt-3.5-turbo")
        self.assertEqual(wrapper.temperature, 0.5)
        self.assertEqual(wrapper.max_tokens, 500)


class TestLangChainWrapperMessageConversion(unittest.TestCase):
    """Test message conversion functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not LANGCHAIN_AVAILABLE:
            self.skipTest("LangChain not available")
        
        from langchain_openai import ChatOpenAI
        mock_model = ChatOpenAI(model="gpt-4o", api_key="test-key")
        self.wrapper = create_langchain_litellm_wrapper(langchain_model=mock_model)
        
        # Import types for testing
        from google.adk.runners import types
        self.Content = types.Content
        self.Part = types.Part
    
    def test_user_message_conversion(self):
        """Test conversion of user message from Google ADK to LangChain format."""
        content = self.Content(
            role="user",
            parts=[self.Part(text="Hello, how are you?")]
        )
        
        message = self.wrapper._convert_content_to_langchain_message(content)
        
        self.assertIsInstance(message, HumanMessage)
        self.assertEqual(message.content, "Hello, how are you?")
    
    def test_assistant_message_conversion(self):
        """Test conversion of assistant message."""
        content = self.Content(
            role="assistant",
            parts=[self.Part(text="I'm doing well, thank you!")]
        )
        
        message = self.wrapper._convert_content_to_langchain_message(content)
        
        self.assertIsInstance(message, AIMessage)
        self.assertEqual(message.content, "I'm doing well, thank you!")
    
    def test_system_message_conversion(self):
        """Test conversion of system message."""
        content = self.Content(
            role="system",
            parts=[self.Part(text="You are a helpful assistant.")]
        )
        
        message = self.wrapper._convert_content_to_langchain_message(content)
        
        self.assertIsInstance(message, SystemMessage)
        self.assertEqual(message.content, "You are a helpful assistant.")
    
    def test_multiple_parts_conversion(self):
        """Test conversion of content with multiple text parts."""
        content = self.Content(
            role="user",
            parts=[
                self.Part(text="Hello"),
                self.Part(text="How are you?")
            ]
        )
        
        message = self.wrapper._convert_content_to_langchain_message(content)
        
        self.assertIsInstance(message, HumanMessage)
        self.assertEqual(message.content, "Hello\nHow are you?")


class TestMaybeAppendUserContentComprehensive(unittest.TestCase):
    """Test _maybe_append_user_content functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not LANGCHAIN_AVAILABLE:
            self.skipTest("LangChain not available")
        
        from langchain_openai import ChatOpenAI
        mock_model = ChatOpenAI(model="gpt-4o", api_key="test-key")
        self.wrapper = create_langchain_litellm_wrapper(langchain_model=mock_model)
        
        # Import types for testing
        from google.adk.runners import types
        from google.adk.models import LlmRequest
        self.Content = types.Content
        self.Part = types.Part
        self.LlmRequest = LlmRequest
    
    def test_empty_contents_list(self):
        """Test _maybe_append_user_content with empty contents list."""
        request = self.LlmRequest(contents=[])
        
        self.wrapper._maybe_append_user_content(request)
        
        self.assertEqual(len(request.contents), 1)
        self.assertEqual(request.contents[0].role, 'user')
        self.assertIn("System Instruction", request.contents[0].parts[0].text)
    
    def test_last_message_not_user(self):
        """Test _maybe_append_user_content when last message is not from user."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")])
        ])
        
        original_count = len(request.contents)
        self.wrapper._maybe_append_user_content(request)
        
        self.assertEqual(len(request.contents), original_count + 1)
        self.assertEqual(request.contents[-1].role, 'user')
        self.assertIn("Continue processing", request.contents[-1].parts[0].text)
    
    def test_last_message_is_user(self):
        """Test _maybe_append_user_content when last message is already from user."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")]),
            self.Content(role="user", parts=[self.Part(text="How are you?")])
        ])
        
        original_count = len(request.contents)
        self.wrapper._maybe_append_user_content(request)
        
        # Should not add any new content
        self.assertEqual(len(request.contents), original_count)
        self.assertEqual(request.contents[-1].role, 'user')


class TestLangChainWrapperIntegration(unittest.TestCase):
    """Integration tests for LangChain wrapper with real API calls."""
    
    def setUp(self):
        """Set up test fixtures."""
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
    
    def test_basic_message_handling(self):
        """Test basic message handling with real LangChain model."""
        # Create LangChain model
        langchain_model = init_chat_model("openai:gpt-4o")
        wrapper = create_langchain_litellm_wrapper(
            langchain_model=langchain_model,
            model="gpt-4o",
            max_tokens=50
        )
        
        # Test with simple messages
        test_messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2?")
        ]
        
        # Test the model directly
        if hasattr(wrapper.langchain_model, 'invoke'):
            response = wrapper.langchain_model.invoke(test_messages)
            self.assertTrue(hasattr(response, 'content'))
            self.assertIsInstance(response.content, str)
            self.assertGreater(len(response.content), 0)


if __name__ == '__main__':
    # Set up test environment
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Run tests
    unittest.main(verbosity=2)