#!/usr/bin/env python3
"""
Debug script to test if tools are being recognized by Google ADK agent
"""

import asyncio
from dotenv import load_dotenv
from agent import create_agent
from tools import AVAILABLE_TOOLS
from google.adk.runners import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()


async def debug_agent_tools():
    """Debug agent configuration and tool registration"""
    
    print("🔍 Debugging Google ADK Agent with Tools")
    print("=" * 50)
    
    # Create agent with tools
    agent = create_agent(
        model="openai:gpt-4o", 
        name="DebugAgent",
        tools=AVAILABLE_TOOLS
    )
    
    # Debug agent configuration
    print(f"✅ Agent created: {agent.name}")
    print(f"✅ Agent model: {agent.model}")
    print(f"✅ Agent tools: {len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0}")
    
    if hasattr(agent, 'tools') and agent.tools:
        for i, tool in enumerate(agent.tools):
            print(f"   Tool {i+1}: {type(tool).__name__} - {getattr(tool, 'name', 'unnamed')}")
    
    print(f"✅ Agent instruction length: {len(agent.instruction) if hasattr(agent, 'instruction') else 0}")
    
    # Test with a very direct query
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="DebugAgent",
        agent=agent,
        session_service=session_service
    )
    
    session = await session_service.create_session(
        user_id="debug_user", 
        session_id="debug_session",
        app_name="DebugAgent"
    )
    
    # Very explicit query
    query = "I need you to call the get_taipei_time tool right now to get the current time in Taipei. Please use the tool."
    print(f"\n📝 Debug Query: {query}")
    print("-" * 40)
    
    try:
        message = types.Content(role="user", parts=[{"text": query}])
        
        response_generator = runner.run(
            user_id="debug_user",
            session_id="debug_session",
            new_message=message
        )
        
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
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
        
        # Check if any print statements from tools were triggered
        print(f"\n🔍 Tool call analysis:")
        print("   - If you see debug prints from tools above, they were called")
        print("   - If no debug prints, tools were not invoked")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_agent_tools())