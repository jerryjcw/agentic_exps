#!/usr/bin/env python3
"""
Google ADK Agent with LiteLLM + OpenAI GPT-4o Example

This example demonstrates how to create an agent using Google ADK
with LiteLLM as the model provider to access OpenAI's GPT-4o.
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import types
from google.adk.models.registry import LLMRegistry
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.models.lite_llm import LiteLlm
from litellm import acompletion
import re

load_dotenv()


def create_agent(model="openai:gpt-4o", name="LiteLLMAssistant", instruction=None, tools=None):
    """Create and configure a Google ADK agent with configurable LiteLLM model.
    
    Args:
        model: LiteLLM model string (e.g., "openai:gpt-4o", "anthropic:claude-3-sonnet", "gpt-3.5-turbo")
        name: Agent name
        instruction: System instruction for the agent
        tools: List of tool functions to make available to the agent
    """
    if instruction is None:
        instruction = f"You are a helpful assistant powered by {model} via LiteLLM. Answer questions clearly and concisely."
        if tools:
            instruction += """

You have access to the following tools to provide accurate, real-time information:

1. get_taipei_time: Use this tool when users ask about the current time in Taipei, Taiwan. 
   - Call this for questions like "What time is it in Taipei?", "Current time in Taipei", etc.

2. get_temperature: Use this tool when users ask about weather or temperature for any location.
   - Call this for questions like "What's the weather in [city]?", "Temperature in [location]", "How's the weather in [place]?", etc.
   - This tool requires a location parameter (city name).

IMPORTANT: When a user asks a question that matches these tool capabilities, you MUST call the appropriate tool to get real-time data instead of giving generic responses. Only use tools when the user's question directly relates to time in Taipei or weather/temperature information."""
    
    agent = Agent(
        name=name,
        model=LiteLlm(model='openai/gpt-4o'),
        instruction=instruction,
        tools=tools or []
    )
    return agent


async def run_agent_example(agent=None):
    """Run a simple example with the agent."""
    
    # Create the agent and runner
    if agent is None:
        agent = create_agent()
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="LiteLLMAgentExample",
        agent=agent,
        session_service=session_service
    )
    
    # Create a session for our test
    session = await session_service.create_session(
        user_id="test_user", 
        session_id="test_session",
        app_name="LiteLLMAgentExample"
    )
    
    # Example queries to test the agent
    test_queries = [
        "Hello! What can you help me with?",
        "What is the weather like today?", 
        "Can you help me understand what Google ADK with LiteLLM and OpenAI GPT-4o is?"
    ]
    
    print("🤖 Google ADK Agent with LiteLLM Example")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        print("-" * 30)
        
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
            print("Note: Make sure you have proper API credentials configured.")


async def interactive_mode(agent=None):
    """Run the agent in interactive mode."""
    
    if agent is None:
        agent = create_agent()
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="InteractiveLiteLLMAgent",
        agent=agent,
        session_service=session_service
    )
    
    # Create a session for interactive mode
    session = await session_service.create_session(
        user_id="interactive_user", 
        session_id="interactive_session",
        app_name="InteractiveLiteLLMAgent"
    )
    
    print("🤖 Google ADK Interactive Agent with LiteLLM")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 45)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Create a Content object for the query
            message = types.Content(role="user", parts=[{"text": user_input}])
            
            # Run the agent with the query
            response_generator = runner.run(
                user_id="interactive_user",
                session_id="interactive_session",
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
            
            print(f"🤖 Agent: {response_text}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Google ADK Agent with LiteLLM - A configurable AI agent using Google ADK framework with LiteLLM for multi-provider LLM support",
        epilog="""
Examples:
  python agent.py                                    # Use default GPT-4o
  python agent.py --model gpt-3.5-turbo             # Use GPT-3.5-turbo
  python agent.py --interactive                      # Interactive mode
  python agent.py --with-tools                       # Enable time and weather tools
  python agent.py --interactive --with-tools         # Interactive mode with tools
  python agent.py --model gpt-4 --name MyAgent      # Custom model and name
  LITELLM_MODEL=gpt-4-turbo python agent.py         # Environment variable

Supported Models:
  OpenAI: gpt-4o, gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.
  Other providers supported by LiteLLM (requires proper API keys)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive mode (default: example mode)")
    parser.add_argument("--model", default=os.getenv("LITELLM_MODEL", "openai:gpt-4o"), 
                       help="LiteLLM model to use. Examples: gpt-4o, gpt-3.5-turbo, claude-3-sonnet-20240229")
    parser.add_argument("--name", default="LiteLLMAssistant", 
                       help="Agent name for identification")
    parser.add_argument("--with-tools", action="store_true",
                       help="Enable built-in tools (time and weather)")
    
    args = parser.parse_args()
    
    print(f"🚀 Using model: {args.model}")
    
    # Import tools if requested
    tools = None
    if args.with_tools:
        try:
            from tools import AVAILABLE_TOOLS
            tools = AVAILABLE_TOOLS
            print(f"🔧 Enabled {len(tools)} tools: Taipei time, weather lookup")
        except ImportError as e:
            print(f"⚠️  Could not import tools: {e}")
            print("Make sure tools.py is available and dependencies are installed.")
    
    # Create agent with specified model and optional tools
    print(f"Tools available: {tools is not None}, they are: {tools if tools else 'None'}")
    agent = create_agent(model=args.model, name=args.name, tools=tools)
    
    # Check if we should run in interactive mode
    if args.interactive:
        asyncio.run(interactive_mode(agent))
    else:
        asyncio.run(run_agent_example(agent))