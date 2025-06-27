#!/usr/bin/env python3
"""
Test script to verify _maybe_append_user_content functionality

This script tests the edge cases for _maybe_append_user_content to ensure
it works correctly with the LangChain wrapper.
"""

import os
import sys
from google.adk.runners import types
from google.adk.models import LlmRequest
from langchain.chat_models import init_chat_model
from langchain_litellm_wrapper import create_langchain_litellm_wrapper

# Add the parent directory to sys.path to import gpt_caller
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, 'basics'))

try:
    from gpt_caller import get_api_key
except ImportError:
    def get_api_key(file_path=None):
        _ = file_path
        return os.getenv("OPENAI_API_KEY")

Content = types.Content
Part = types.Part

def test_maybe_append_user_content():
    """Test _maybe_append_user_content functionality"""
    print("🧪 Testing _maybe_append_user_content functionality")
    print("=" * 60)
    
    # Setup API key
    try:
        api_key_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'apikey')
        os.environ["OPENAI_API_KEY"] = get_api_key(file_path=api_key_path)
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ No API key available")
            return False

    # Create wrapper
    langchain_model = init_chat_model("openai:gpt-4o")
    wrapper = create_langchain_litellm_wrapper(langchain_model=langchain_model)
    
    print("✓ Created LangChain wrapper")

    # Test Case 1: Empty contents list
    print("\n📝 Test 1: Empty contents list")
    request1 = LlmRequest(contents=[])
    print(f"Before: {len(request1.contents)} contents")
    wrapper._maybe_append_user_content(request1)
    print(f"After: {len(request1.contents)} contents")
    
    if request1.contents and request1.contents[0].role == 'user':
        print("✅ Test 1 PASSED: User content added to empty list")
        print(f"Added content: {request1.contents[0].parts[0].text}")
    else:
        print("❌ Test 1 FAILED: User content not added correctly")
        return False

    # Test Case 2: Last message is not from user (assistant message)
    print("\n📝 Test 2: Last message is assistant message")
    request2 = LlmRequest(contents=[
        Content(role="user", parts=[Part(text="Hello")]),
        Content(role="assistant", parts=[Part(text="Hi there!")])
    ])
    print(f"Before: {len(request2.contents)} contents, last role: {request2.contents[-1].role}")
    wrapper._maybe_append_user_content(request2)
    print(f"After: {len(request2.contents)} contents, last role: {request2.contents[-1].role}")
    
    if len(request2.contents) == 3 and request2.contents[-1].role == 'user':
        print("✅ Test 2 PASSED: User content added after assistant message")
        print(f"Added content: {request2.contents[-1].parts[0].text}")
    else:
        print("❌ Test 2 FAILED: User content not added correctly after assistant message")
        return False

    # Test Case 3: Last message is already from user (should not add)
    print("\n📝 Test 3: Last message is already user message")
    request3 = LlmRequest(contents=[
        Content(role="user", parts=[Part(text="Hello")]),
        Content(role="assistant", parts=[Part(text="Hi there!")]),
        Content(role="user", parts=[Part(text="How are you?")])
    ])
    original_count = len(request3.contents)
    print(f"Before: {original_count} contents, last role: {request3.contents[-1].role}")
    wrapper._maybe_append_user_content(request3)
    print(f"After: {len(request3.contents)} contents, last role: {request3.contents[-1].role}")
    
    if len(request3.contents) == original_count and request3.contents[-1].role == 'user':
        print("✅ Test 3 PASSED: No content added when last message is already user")
    else:
        print("❌ Test 3 FAILED: Content incorrectly modified when last message was user")
        return False

    print("\n🎉 All _maybe_append_user_content tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_maybe_append_user_content()
        if success:
            print("\n✅ All tests completed successfully")
        else:
            print("\n❌ Some tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()