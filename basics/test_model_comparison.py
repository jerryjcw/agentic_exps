#!/usr/bin/env python3
"""
Model Comparison Test

This script tests the behavior consistency between LiteLlm and LangChainLiteLLMWrapper
to ensure they provide similar responses to the same queries.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import types

# Import the agent creation function
from agent import create_agent

load_dotenv()

# Import tools if available
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
    from tools.gadk.tools import AVAILABLE_TOOLS
    TOOLS_AVAILABLE = True
except ImportError:
    AVAILABLE_TOOLS = None
    TOOLS_AVAILABLE = False
    print("⚠️  Tools not available for comparison test")

async def test_agent_with_queries(agent, agent_name, test_queries):
    """Test an agent with a series of queries and return responses."""
    
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=f"ComparisonTest_{agent_name}",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        user_id=f"test_user_{agent_name.lower()}",
        session_id=f"test_session_{agent_name.lower()}",
        app_name=f"ComparisonTest_{agent_name}"
    )
    
    responses = []
    
    print(f"\n🤖 Testing {agent_name}")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        
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
            
            responses.append({
                'query': query,
                'response': response_text.strip(),
                'tool_calls': tool_calls,
                'length': len(response_text.strip())
            })
            
            print(f"📥 Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            if tool_calls:
                print(f"🔧 Tools used: {', '.join(tool_calls)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            responses.append({
                'query': query,
                'response': f"ERROR: {str(e)}",
                'tool_calls': [],
                'length': 0
            })
    
    return responses

async def compare_model_behaviors():
    """Compare the behavior of LiteLlm vs LangChain wrapper."""
    
    print("🔄 Model Behavior Comparison Test")
    print("=" * 60)
    print("This test compares LiteLlm vs LangChain wrapper behavior")
    
    # Test queries covering different scenarios
    test_queries = [
        "Hello! What's your name?",
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "Write a short poem about coding.",
        "What is 15 * 23?",
        "Tell me a joke about programming."
    ]
    
    # Add tool-based queries if tools are available
    if TOOLS_AVAILABLE and AVAILABLE_TOOLS:
        test_queries.extend([
            "What time is it in Taipei right now?",
            "What's the weather like in Tokyo?"
        ])
        tools = AVAILABLE_TOOLS
        print(f"✓ Using {len(tools)} tools for testing")
    else:
        tools = None
        print("⚠️  No tools available for testing")
    
    print(f"\n📋 Testing with {len(test_queries)} queries")
    
    try:
        # Create agents with both backends
        print("\n🏗️  Creating agents...")
        
        litellm_agent = create_agent(
            model="openai:gpt-4o",
            name="LiteLLM_Agent",
            tools=tools,
            use_langchain=False
        )
        print("✓ Created LiteLLM agent")
        
        langchain_agent = create_agent(
            model="openai:gpt-4o", 
            name="LangChain_Agent",
            tools=tools,
            use_langchain=True
        )
        print("✓ Created LangChain wrapper agent")
        
        # Test both agents
        litellm_responses = await test_agent_with_queries(litellm_agent, "LiteLLM", test_queries)
        langchain_responses = await test_agent_with_queries(langchain_agent, "LangChain", test_queries)
        
        # Compare results
        print("\n📊 Comparison Results")
        print("=" * 60)
        
        successful_comparisons = 0
        total_comparisons = len(test_queries)
        
        for i, (lite_resp, lang_resp) in enumerate(zip(litellm_responses, langchain_responses)):
            print(f"\n📝 Query {i+1}: {lite_resp['query']}")
            print("-" * 40)
            
            # Check if both succeeded
            lite_success = not lite_resp['response'].startswith('ERROR:')
            lang_success = not lang_resp['response'].startswith('ERROR:')
            
            print(f"LiteLLM Success: {'✅' if lite_success else '❌'}")
            print(f"LangChain Success: {'✅' if lang_success else '❌'}")
            
            if lite_success and lang_success:
                successful_comparisons += 1
                
                # Compare response lengths (should be reasonably similar)
                length_diff = abs(lite_resp['length'] - lang_resp['length'])
                length_ratio = length_diff / max(lite_resp['length'], lang_resp['length'], 1)
                
                print(f"Response length difference: {length_diff} chars ({length_ratio:.2%})")
                
                # Compare tool usage
                lite_tools = set(lite_resp['tool_calls'])
                lang_tools = set(lang_resp['tool_calls'])
                
                if lite_tools == lang_tools:
                    print("🔧 Tool usage: ✅ Identical")
                else:
                    print(f"🔧 Tool usage: ⚠️  Different")
                    print(f"   LiteLLM: {lite_tools}")
                    print(f"   LangChain: {lang_tools}")
                
                # Show first 100 chars of each response
                print(f"LiteLLM response: {lite_resp['response'][:100]}...")
                print(f"LangChain response: {lang_resp['response'][:100]}...")
                
            else:
                print("❌ One or both agents failed for this query")
                if not lite_success:
                    print(f"LiteLLM error: {lite_resp['response']}")
                if not lang_success:
                    print(f"LangChain error: {lang_resp['response']}")
        
        # Final summary
        print(f"\n🎯 Final Results")
        print("=" * 30)
        print(f"Successful comparisons: {successful_comparisons}/{total_comparisons}")
        
        success_rate = successful_comparisons / total_comparisons
        if success_rate >= 0.8:
            print("✅ Models show consistent behavior!")
        elif success_rate >= 0.6:
            print("⚠️  Models show mostly consistent behavior")
        else:
            print("❌ Models show inconsistent behavior")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_consecutive_conversations():
    """Test that both models handle consecutive conversations properly."""
    
    print("\n💬 Consecutive Conversation Test")
    print("=" * 50)
    
    consecutive_queries = [
        "Hello, my name is Alice.",
        "What is my name?", 
        "Can you remember what I just told you?",
        "What is 10 + 5?",
        "What was the previous calculation result?",
        "Thank you for helping me!"
    ]
    
    try:
        # Test both agents
        litellm_agent = create_agent(use_langchain=False)
        langchain_agent = create_agent(use_langchain=True)
        
        print("Testing LiteLLM agent...")
        litellm_responses = await test_agent_with_queries(litellm_agent, "LiteLLM_Consecutive", consecutive_queries)
        
        print("\nTesting LangChain agent...")
        langchain_responses = await test_agent_with_queries(langchain_agent, "LangChain_Consecutive", consecutive_queries)
        
        # Check memory consistency
        memory_tests = [
            (1, "name"),  # Should remember Alice
            (2, "remember"),  # Should show memory capability
            (4, "15"),  # Should remember calculation result
        ]
        
        print("\n🧠 Memory Consistency Check")
        print("-" * 30)
        
        for query_index, expected_content in memory_tests:
            lite_resp = litellm_responses[query_index]['response'].lower()
            lang_resp = langchain_responses[query_index]['response'].lower()
            
            lite_has_content = expected_content.lower() in lite_resp
            lang_has_content = expected_content.lower() in lang_resp
            
            print(f"Query {query_index + 1} - Looking for '{expected_content}':")
            print(f"  LiteLLM: {'✅' if lite_has_content else '❌'}")
            print(f"  LangChain: {'✅' if lang_has_content else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Consecutive conversation test failed: {e}")
        return False

async def main():
    """Run all comparison tests."""
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found. Please set your API key.")
        return
    
    print("🚀 Starting Model Comparison Tests")
    print("=" * 60)
    
    # Run behavior comparison
    behavior_success = await compare_model_behaviors()
    
    # Run consecutive conversation test
    consecutive_success = await test_consecutive_conversations()
    
    print("\n🏁 Final Test Summary")
    print("=" * 40)
    print(f"Behavior Comparison: {'✅ PASS' if behavior_success else '❌ FAIL'}")
    print(f"Consecutive Conversations: {'✅ PASS' if consecutive_success else '❌ FAIL'}")
    
    if behavior_success and consecutive_success:
        print("\n🎉 All tests passed! LangChain wrapper behaves consistently with LiteLlm.")
    else:
        print("\n⚠️  Some tests failed. Check the results above.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()