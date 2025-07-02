#!/usr/bin/env python3
"""
Test script to demonstrate Google ADK agent with tools
"""

import asyncio
from dotenv import load_dotenv
from agent import create_agent, run_agent_example
from tools import AVAILABLE_TOOLS
from google.adk.runners import types




async def test_agent_with_tools():
    """Test the agent with tool-related queries"""
    
    # Create agent with tools
    agent = create_agent(
        model="openai:gpt-4o", 
        name="ToolTestAgent",
        tools=AVAILABLE_TOOLS,
        instruction="You are a helpful assistant with access to tools for getting current time in Taipei and weather information. Use these tools when appropriate to answer user questions."
    )
    
    # Test queries that should trigger tool usage
    test_queries = [
        "What time is it in Taipei right now?",
        "Can you tell me the current time in Taipei, Taiwan?",
        "What's the weather like in New York?",
        "Get me the temperature in London",
        "What's the weather in Tokyo?"
    ]
    
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    
    # Create session and runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="ToolTestAgent",
        agent=agent,
        session_service=session_service
    )
    
    # Create a session
    session = await session_service.create_session(
        user_id="test_user", 
        session_id="test_session",
        app_name="ToolTestAgent"
    )
    
    print("🔧 Testing Google ADK Agent with Tools")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Create a Content object for the query
            message = types.Content(role="user", parts=[{"text": query}])
            
            # Run the agent with the query
            response_generator = runner.run(
                user_id="test_user",
                session_id="test_session",
                new_message=message
            )
            
            # Collect the response
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content:
                    # Extract text from Content object properly
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                    else:
                        response_text += str(event.content)
                elif hasattr(event, 'text'):
                    response_text += event.text
                elif str(event):
                    response_text += str(event)
            
            print(f"🤖 Response: {response_text}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Tool testing completed!")


if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())