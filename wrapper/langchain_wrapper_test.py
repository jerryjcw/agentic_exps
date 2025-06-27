#!/usr/bin/env python3
"""
Test script for LangChain LiteLLM Wrapper

This script demonstrates how to use the LangChain LiteLLM wrapper with a 
LangChain model initialized using init_chat_model.
"""

import os
import sys
import asyncio
from langchain.chat_models import init_chat_model
from langchain_litellm_wrapper import create_langchain_litellm_wrapper, LangChainLiteLLMWrapper
from google.adk.runners import types

# Add the parent directory to sys.path to import gpt_caller
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, 'basics'))

try:
    from gpt_caller import get_api_key
except ImportError:
    print("Warning: Could not import gpt_caller, using environment variable for API key")
    def get_api_key(file_path=None):
        _ = file_path  # Unused parameter
        return os.getenv("OPENAI_API_KEY")

Content = types.Content
Part = types.Part


async def test_langchain_wrapper():
    """Test the LangChain LiteLLM wrapper with a simple conversation."""
    
    # Setup API key (you may need to adjust the path)
    try:
        api_key_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'apikey')
        os.environ["OPENAI_API_KEY"] = get_api_key(file_path=api_key_path)
    except Exception as e:
        print(f"Warning: Could not load API key: {e}")
        print("Please ensure OPENAI_API_KEY environment variable is set")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("No API key available, skipping full test")
            return False
    
    # Create LangChain model using init_chat_model
    try:
        langchain_model = init_chat_model("openai:gpt-4o")
        print(f"✓ Created LangChain model: {langchain_model}")
    except Exception as e:
        print(f"❌ Failed to create LangChain model: {e}")
        return False
    
    # Create the wrapper
    try:
        wrapper = create_langchain_litellm_wrapper(
            langchain_model=langchain_model,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=150
        )
        print(f"✓ Created wrapper: {wrapper}")
    except Exception as e:
        print(f"❌ Failed to create wrapper: {e}")
        return False
    
    # Test basic message conversion
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Create test messages
        test_messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello! Can you tell me a short joke?")
        ]
        
        print("\n📤 Testing message handling...")
        print(f"Input messages: {len(test_messages)} messages")
        
        # Test the model directly (not through the full ADK interface)
        if hasattr(wrapper.langchain_model, 'ainvoke'):
            response = await wrapper.langchain_model.ainvoke(test_messages)
        else:
            response = wrapper.langchain_model.invoke(test_messages)
        
        print(f"✓ LangChain model response: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wrapper_creation():
    """Test that the wrapper can be created without errors."""
    try:
        # This is a basic test that doesn't require API keys
        from langchain_openai import ChatOpenAI
        
        # Create a mock LangChain model (won't work without API key, but tests creation)
        mock_model = ChatOpenAI(model="gpt-4o", api_key="test-key")
        
        # Create the wrapper
        wrapper = create_langchain_litellm_wrapper(
            langchain_model=mock_model,
            model="gpt-4o"
        )
        
        print("✓ Wrapper creation test passed")
        print(f"  - Wrapper model: {wrapper.model}")
        print(f"  - Wrapper temperature: {wrapper.temperature}")
        print(f"  - Wrapper max_tokens: {wrapper.max_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Wrapper creation test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing LangChain LiteLLM Wrapper")
    print("=" * 50)
    
    # Test 1: Basic wrapper creation
    print("\n1. Testing wrapper creation...")
    creation_success = test_wrapper_creation()
    
    if creation_success:
        print("\n2. Testing async conversation...")
        # Test 2: Full async conversation (requires API key)
        try:
            asyncio.run(test_langchain_wrapper())
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted by user")
        except Exception as e:
            print(f"\n⚠️  Async test skipped due to: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")