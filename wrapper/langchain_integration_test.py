#!/usr/bin/env python3
"""
Integration test for LangChain LiteLLM Wrapper with Google ADK Agents

This test demonstrates how to use the LangChain wrapper with Google ADK agents.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk import Runner  
from google.adk.sessions import InMemorySessionService
from google.adk.runners import types

# Import our wrapper
from langchain_litellm_wrapper import create_langchain_litellm_wrapper
from langchain.chat_models import init_chat_model

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

load_dotenv()

# Import tools from the tools.gadk.tools module  
sys.path.append(project_root)
from tools.gadk.tools import google_search_tool, temperature_tool, taipei_time_tool

def create_langchain_wrapper_model(api_key_file: str = None, model: str = "gpt-4o"):
    """
    Create a LangChain LiteLLM wrapper model.
    
    Args:
        api_key_file: Path to API key file (optional, uses env var if None)
        model: Model name to use (default: gpt-4o)
        
    Returns:
        LangChainLiteLLMWrapper instance
    """
    # Setup API key
    if api_key_file:
        try:
            os.environ["OPENAI_API_KEY"] = get_api_key(file_path=api_key_file)
        except Exception as e:
            print(f"Warning: Could not load API key from file: {e}")
    
    # Create LangChain model
    langchain_model = init_chat_model("openai:gpt-4o")
    
    # Create the wrapper
    wrapper_model = create_langchain_litellm_wrapper(
        langchain_model=langchain_model,
        model=model,
        temperature=0.7,
        max_tokens=1000
    )
    
    return wrapper_model


def create_simple_agent_with_langchain_wrapper():
    """Create a simple agent using the LangChain wrapper"""
    
    # Create the wrapped model
    model = create_langchain_wrapper_model()
    
    instruction = """You are a helpful assistant. Answer questions clearly and concisely.
    If you don't know something, say so honestly."""
    
    # Create agent with wrapper model
    agent = Agent(
        name="LangChainWrapperAgent",
        model=model,
        instruction=instruction
    )
    
    return agent


def create_agent_with_tools():
    """Create an agent with tools using the LangChain wrapper"""
    
    # Create the wrapped model
    model = create_langchain_wrapper_model()
    
    instruction = """You are a helpful assistant with access to various tools.
    
    Available tools:
    1. google_search - Search the web for information
    2. temperature_tool - Get current weather and temperature for any location
    3. taipei_time_tool - Get current time in Taipei, Taiwan
    
    When a user asks for information that requires these tools, use them appropriately.
    Always be helpful and provide comprehensive answers using the tool results."""
    
    # Create agent with wrapper model and tools
    agent = Agent(
        name="LangChainToolAgent",
        model=model,
        instruction=instruction,
        tools=[google_search_tool, temperature_tool, taipei_time_tool]
    )
    
    return agent


async def test_simple_agent():
    """Test the simple agent with LangChain wrapper"""
    print("🤖 Testing Simple Agent with LangChain Wrapper")
    print("=" * 50)
    
    try:
        # Create agent
        agent = create_simple_agent_with_langchain_wrapper()
        print("✓ Created agent with LangChain wrapper")
        
        # Set up runner
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="LangChainWrapperTest",
            agent=agent,
            session_service=session_service
        )
        print("✓ Created runner")
        
        # Create session
        await session_service.create_session(
            user_id="test_user",
            session_id="test_session",
            app_name="LangChainWrapperTest"
        )
        print("✓ Created session")
        
        # Test query
        test_query = "What is the capital of France?"
        message = types.Content(role="user", parts=[types.Part(text=test_query)])
        
        print(f"📤 Query: {test_query}")
        print("📥 Response:", end=" ")
        
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
                            print(part.text, end="")
        
        print("\n")
        
        if response_text.strip():
            print("✅ Test PASSED: Received response from LangChain wrapper")
            return True
        else:
            print("❌ Test FAILED: No response received")
            return False
            
    except Exception as e:
        print(f"❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversation():
    """Test a multi-turn conversation"""
    print("\n💬 Testing Multi-turn Conversation")
    print("=" * 50)
    
    try:
        # Create agent
        agent = create_simple_agent_with_langchain_wrapper()
        
        # Set up runner
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="LangChainConversationTest",
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        await session_service.create_session(
            user_id="conv_user",
            session_id="conv_session",
            app_name="LangChainConversationTest"
        )
        
        # Test queries
        queries = [
            "Hello, my name is Alice.",
            "What is my name?",
            "Can you tell me a joke about programming?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📤 Turn {i}: {query}")
            message = types.Content(role="user", parts=[types.Part(text=query)])
            
            print("📥 Response:", end=" ")
            
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
                                print(part.text, end="")
            
            print()
            
            if not response_text.strip():
                print(f"❌ No response for turn {i}")
                return False
        
        print("\n✅ Conversation test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Conversation test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_usage():
    """Test tool usage capabilities with the LangChain wrapper"""
    print("\n🛠️ Testing Tool Usage with LangChain Wrapper")
    print("=" * 50)
    
    try:
        # Create agent with tools
        agent = create_agent_with_tools()
        print("✓ Created agent with tools (google_search, temperature, taipei_time)")
        
        # Set up runner
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="LangChainToolTest",
            agent=agent,
            session_service=session_service
        )
        print("✓ Created runner")
        
        # Create session
        await session_service.create_session(
            user_id="tool_user",
            session_id="tool_session",
            app_name="LangChainToolTest"
        )
        print("✓ Created session")
        
        # Test queries that should trigger tool usage
        test_queries = [
            {
                "query": "What time is it in Taipei right now?",
                "expected_tool": "taipei_time_tool",
                "description": "Testing Taipei time tool"
            },
            {
                "query": "What's the current weather in Tokyo?",
                "expected_tool": "temperature_tool", 
                "description": "Testing temperature tool"
            },
            {
                "query": "Search for information about the latest Python version",
                "expected_tool": "google_search_tool",
                "description": "Testing Google search tool"
            }
        ]
        
        successful_tests = 0
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📤 Test {i}: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            
            message = types.Content(role="user", parts=[types.Part(text=test_case['query'])])
            
            print("📥 Response:", end=" ")
            
            try:
                response_generator = runner.run(
                    user_id="tool_user",
                    session_id="tool_session",
                    new_message=message
                )
                
                response_text = ""
                tool_calls_detected = False
                
                for event in response_generator:
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                    print(part.text, end="")
                                elif hasattr(part, 'function_call') and part.function_call:
                                    tool_calls_detected = True
                                    print(f"\n🔧 Tool called: {part.function_call.name}")
                
                print("\n")
                
                if response_text.strip():
                    print(f"✅ Test {i} PASSED: Received response")
                    if tool_calls_detected:
                        print(f"🛠️ Tool usage detected (expected: {test_case['expected_tool']})")
                    successful_tests += 1
                else:
                    print(f"❌ Test {i} FAILED: No response received")
                    
            except Exception as e:
                print(f"\n❌ Test {i} FAILED: {str(e)}")
        
        print(f"\n📊 Tool usage test results: {successful_tests}/{len(test_queries)} tests passed")
        
        if successful_tests == len(test_queries):
            print("✅ All tool usage tests PASSED")
            return True
        else:
            print("⚠️ Some tool usage tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Tool usage test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    print("🚀 LangChain LiteLLM Wrapper Integration Tests")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'apikey')
            api_key = get_api_key(file_path=api_key_path)
            os.environ["OPENAI_API_KEY"] = api_key
        except Exception:
            print("❌ No API key available. Please set OPENAI_API_KEY environment variable")
            return
    
    print("✓ API key found")
    
    # Test simple agent
    success1 = await test_simple_agent()
    
    # Test conversation
    success2 = await test_conversation()
    
    # Test tool usage
    success3 = await test_tool_usage()
    
    print("\n📊 Test Results:")
    print(f"Simple Agent: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Conversation: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Tool Usage: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 All integration tests passed! The LangChain wrapper is working correctly with Google ADK including tool usage.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()