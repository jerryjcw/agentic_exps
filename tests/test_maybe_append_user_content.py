#!/usr/bin/env python3
"""
Comprehensive tests for _maybe_append_user_content functionality

This module contains the exact equivalent of the original test_maybe_append_user_content.py
to ensure the functionality works correctly with both LangChain and OpenAI wrappers.
"""

import os
import sys
import unittest

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wrapper_dir = os.path.join(project_root, 'wrapper')
basics_dir = os.path.join(project_root, 'basics')
sys.path.extend([wrapper_dir, basics_dir])

try:
    from google.adk.runners import types
    from google.adk.models import LlmRequest
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
    from openai_litellm_wrapper import create_openai_litellm_wrapper
    from gpt_caller import get_openai_client
    OPENAI_WRAPPER_AVAILABLE = True
except ImportError as e:
    OPENAI_WRAPPER_AVAILABLE = False
    print(f"Warning: OpenAI wrapper not available: {e}")

try:
    from gpt_caller import get_api_key
except ImportError:
    def get_api_key(file_path=None):
        return os.getenv("OPENAI_API_KEY")


class BaseMaybeAppendUserContentTest(unittest.TestCase):
    """Base class for _maybe_append_user_content tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not GOOGLE_ADK_AVAILABLE:
            self.skipTest("Google ADK not available")
        
        # Setup API key
        try:
            api_key_path = os.path.join(project_root, 'config', 'apikey')
            os.environ["OPENAI_API_KEY"] = get_api_key(file_path=api_key_path)
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.skipTest("No API key available")

        # Import types for testing
        self.Content = types.Content
        self.Part = types.Part
        self.LlmRequest = LlmRequest


class TestLangChainMaybeAppendUserContent(BaseMaybeAppendUserContentTest):
    """Test _maybe_append_user_content functionality with LangChain wrapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        if not LANGCHAIN_AVAILABLE:
            self.skipTest("LangChain not available")
        
        # Create LangChain wrapper
        langchain_model = init_chat_model("openai:gpt-4o")
        self.wrapper = create_langchain_litellm_wrapper(langchain_model=langchain_model)
    
    def test_maybe_append_user_content_empty_contents(self):
        """Test _maybe_append_user_content with empty contents list."""
        request = self.LlmRequest(contents=[])
        
        print(f"Before: {len(request.contents)} contents")
        self.wrapper._maybe_append_user_content(request)
        print(f"After: {len(request.contents)} contents")
        
        self.assertEqual(len(request.contents), 1)
        self.assertEqual(request.contents[0].role, 'user')
        self.assertIn("System Instruction", request.contents[0].parts[0].text)
        print(f"Added content: {request.contents[0].parts[0].text}")
    
    def test_maybe_append_user_content_last_assistant(self):
        """Test _maybe_append_user_content when last message is assistant message."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")])
        ])
        
        original_count = len(request.contents)
        last_role_before = request.contents[-1].role
        print(f"Before: {original_count} contents, last role: {last_role_before}")
        
        self.wrapper._maybe_append_user_content(request)
        
        print(f"After: {len(request.contents)} contents, last role: {request.contents[-1].role}")
        
        self.assertEqual(len(request.contents), original_count + 1)
        self.assertEqual(request.contents[-1].role, 'user')
        self.assertIn("Continue processing", request.contents[-1].parts[0].text)
        print(f"Added content: {request.contents[-1].parts[0].text}")
    
    def test_maybe_append_user_content_last_user(self):
        """Test _maybe_append_user_content when last message is already user message."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")]),
            self.Content(role="user", parts=[self.Part(text="How are you?")])
        ])
        
        original_count = len(request.contents)
        last_role_before = request.contents[-1].role
        print(f"Before: {original_count} contents, last role: {last_role_before}")
        
        self.wrapper._maybe_append_user_content(request)
        
        print(f"After: {len(request.contents)} contents, last role: {request.contents[-1].role}")
        
        # Should not add any new content
        self.assertEqual(len(request.contents), original_count)
        self.assertEqual(request.contents[-1].role, 'user')


@unittest.skipUnless(OPENAI_WRAPPER_AVAILABLE, "OpenAI wrapper not available")
class TestOpenAIMaybeAppendUserContent(BaseMaybeAppendUserContentTest):
    """Test _maybe_append_user_content functionality with OpenAI wrapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create OpenAI wrapper
        openai_client = get_openai_client(None)
        self.wrapper = create_openai_litellm_wrapper(
            openai_client=openai_client,
            model="gpt-4o"
        )
    
    def test_maybe_append_user_content_empty_contents(self):
        """Test _maybe_append_user_content with empty contents list."""
        request = self.LlmRequest(contents=[])
        
        print(f"Before: {len(request.contents)} contents")
        self.wrapper._maybe_append_user_content(request)
        print(f"After: {len(request.contents)} contents")
        
        self.assertEqual(len(request.contents), 1)
        self.assertEqual(request.contents[0].role, 'user')
        self.assertIn("System Instruction", request.contents[0].parts[0].text)
        print(f"Added content: {request.contents[0].parts[0].text}")
    
    def test_maybe_append_user_content_last_assistant(self):
        """Test _maybe_append_user_content when last message is assistant message."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")])
        ])
        
        original_count = len(request.contents)
        last_role_before = request.contents[-1].role
        print(f"Before: {original_count} contents, last role: {last_role_before}")
        
        self.wrapper._maybe_append_user_content(request)
        
        print(f"After: {len(request.contents)} contents, last role: {request.contents[-1].role}")
        
        self.assertEqual(len(request.contents), original_count + 1)
        self.assertEqual(request.contents[-1].role, 'user')
        self.assertIn("Continue processing", request.contents[-1].parts[0].text)
        print(f"Added content: {request.contents[-1].parts[0].text}")
    
    def test_maybe_append_user_content_last_user(self):
        """Test _maybe_append_user_content when last message is already user message."""
        request = self.LlmRequest(contents=[
            self.Content(role="user", parts=[self.Part(text="Hello")]),
            self.Content(role="assistant", parts=[self.Part(text="Hi there!")]),
            self.Content(role="user", parts=[self.Part(text="How are you?")])
        ])
        
        original_count = len(request.contents)
        last_role_before = request.contents[-1].role
        print(f"Before: {original_count} contents, last role: {last_role_before}")
        
        self.wrapper._maybe_append_user_content(request)
        
        print(f"After: {len(request.contents)} contents, last role: {request.contents[-1].role}")
        
        # Should not add any new content
        self.assertEqual(len(request.contents), original_count)
        self.assertEqual(request.contents[-1].role, 'user')


class TestMaybeAppendUserContentFunctionality(BaseMaybeAppendUserContentTest):
    """Test the overall _maybe_append_user_content functionality as in original test."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Try to create both wrappers
        self.langchain_wrapper = None
        self.openai_wrapper = None
        
        if LANGCHAIN_AVAILABLE:
            try:
                langchain_model = init_chat_model("openai:gpt-4o")
                self.langchain_wrapper = create_langchain_litellm_wrapper(langchain_model=langchain_model)
                print("✓ Created LangChain wrapper")
            except Exception as e:
                print(f"Failed to create LangChain wrapper: {e}")
        
        if OPENAI_WRAPPER_AVAILABLE:
            try:
                openai_client = get_openai_client(None)
                self.openai_wrapper = create_openai_litellm_wrapper(
                    openai_client=openai_client,
                    model="gpt-4o"
                )
                print("✓ Created OpenAI wrapper")
            except Exception as e:
                print(f"Failed to create OpenAI wrapper: {e}")
        
        if not self.langchain_wrapper and not self.openai_wrapper:
            self.skipTest("No wrappers available for testing")
    
    def test_all_maybe_append_user_content_scenarios(self):
        """Test all _maybe_append_user_content scenarios with all available wrappers."""
        print("🧪 Testing _maybe_append_user_content functionality")
        print("=" * 60)
        
        wrappers = []
        if self.langchain_wrapper:
            wrappers.append(("LangChain", self.langchain_wrapper))
        if self.openai_wrapper:
            wrappers.append(("OpenAI", self.openai_wrapper))
        
        for wrapper_name, wrapper in wrappers:
            with self.subTest(wrapper=wrapper_name):
                print(f"\n🔧 Testing {wrapper_name} wrapper:")
                
                # Test Case 1: Empty contents list
                print("\n📝 Test 1: Empty contents list")
                request1 = self.LlmRequest(contents=[])
                print(f"Before: {len(request1.contents)} contents")
                wrapper._maybe_append_user_content(request1)
                print(f"After: {len(request1.contents)} contents")
                
                self.assertEqual(len(request1.contents), 1)
                self.assertEqual(request1.contents[0].role, 'user')
                print(f"✅ Test 1 PASSED: User content added to empty list")
                print(f"Added content: {request1.contents[0].parts[0].text}")
                
                # Test Case 2: Last message is not from user (assistant message)
                print("\n📝 Test 2: Last message is assistant message")
                request2 = self.LlmRequest(contents=[
                    self.Content(role="user", parts=[self.Part(text="Hello")]),
                    self.Content(role="assistant", parts=[self.Part(text="Hi there!")])
                ])
                print(f"Before: {len(request2.contents)} contents, last role: {request2.contents[-1].role}")
                wrapper._maybe_append_user_content(request2)
                print(f"After: {len(request2.contents)} contents, last role: {request2.contents[-1].role}")
                
                self.assertEqual(len(request2.contents), 3)
                self.assertEqual(request2.contents[-1].role, 'user')
                print(f"✅ Test 2 PASSED: User content added after assistant message")
                print(f"Added content: {request2.contents[-1].parts[0].text}")
                
                # Test Case 3: Last message is already from user (should not add)
                print("\n📝 Test 3: Last message is already user message")
                request3 = self.LlmRequest(contents=[
                    self.Content(role="user", parts=[self.Part(text="Hello")]),
                    self.Content(role="assistant", parts=[self.Part(text="Hi there!")]),
                    self.Content(role="user", parts=[self.Part(text="How are you?")])
                ])
                original_count = len(request3.contents)
                print(f"Before: {original_count} contents, last role: {request3.contents[-1].role}")
                wrapper._maybe_append_user_content(request3)
                print(f"After: {len(request3.contents)} contents, last role: {request3.contents[-1].role}")
                
                self.assertEqual(len(request3.contents), original_count)
                self.assertEqual(request3.contents[-1].role, 'user')
                print(f"✅ Test 3 PASSED: No content added when last message is already user")
        
        print("\n🎉 All _maybe_append_user_content tests passed!")


if __name__ == '__main__':
    # Set up test environment
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Run tests
    unittest.main(verbosity=2)