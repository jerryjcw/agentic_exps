"""
LLM Utility Functions for Agent Optimizer

Simple utility functions that use Google ADK agents following established
patterns from core/*.py, replacing direct LiteLLM calls with proper
Google ADK agent execution.
"""

import asyncio
import logging
from typing import Optional

# Google ADK imports following core/*.py patterns
from google.adk.agents import Agent
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

async def call_evaluation_agent(
    evaluation_prompt: str,
    system_instruction: str,
    model_name: str = "openai/gpt-4o"
) -> str:
    """
    Call an evaluation agent using Google ADK patterns.
    
    Args:
        evaluation_prompt: The evaluation prompt with actual/expected outputs
        system_instruction: System instruction for the agent
        model_name: Model to use (respects the model_name parameter)
        
    Returns:
        Response text from the agent
    """
    try:
        # Create agent following core/*.py patterns
        agent = Agent(
            name="EvaluationAgent",
            model=LiteLlm(model=model_name),
            instruction=system_instruction
        )
        
        # Use established session management pattern
        session_service = InMemorySessionService()
        runner = Runner(
            app_name='AgentOptimizer',
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            user_id='optimizer',
            session_id='evaluation_session',
            app_name='AgentOptimizer'
        )
        
        # Create message following types.Content pattern
        message = types.Content(role="user", parts=[{"text": evaluation_prompt}])
        
        # Run agent following established pattern
        response_generator = runner.run(
            user_id='optimizer',
            session_id='evaluation_session',
            new_message=message
        )
        
        # Extract response following flexible_agents.py pattern
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if event.is_final_response():
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error in evaluation agent: {str(e)}")
        return ""

async def call_suggestion_agent(
    suggestion_prompt: str,
    system_instruction: str,
    model_name: str = "openai/gpt-4o"
) -> str:
    """
    Call a suggestion generation agent using Google ADK patterns.
    
    Args:
        suggestion_prompt: The suggestion generation prompt
        system_instruction: System instruction for the agent
        model_name: Model to use (respects the model_name parameter)
        
    Returns:
        Response text from the agent
    """
    try:
        # Create agent following core/*.py patterns
        agent = Agent(
            name="SuggestionAgent",
            model=LiteLlm(model=model_name),
            instruction=system_instruction
        )
        
        # Use established session management pattern
        session_service = InMemorySessionService()
        runner = Runner(
            app_name='AgentOptimizer',
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            user_id='optimizer',
            session_id='suggestion_session',
            app_name='AgentOptimizer'
        )
        
        # Create message following types.Content pattern
        message = types.Content(role="user", parts=[{"text": suggestion_prompt}])
        
        # Run agent following established pattern
        response_generator = runner.run(
            user_id='optimizer',
            session_id='suggestion_session',
            new_message=message
        )
        
        # Extract response following flexible_agents.py pattern
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if event.is_final_response():
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error in suggestion agent: {str(e)}")
        return ""

async def call_generic_llm_agent(
    prompt: str,
    system_instruction: str,
    model_name: str = "openai/gpt-4o",
    agent_name: str = "UtilityAgent"
) -> str:
    """
    Call a generic LLM agent using Google ADK patterns.
    
    Args:
        prompt: The user prompt
        system_instruction: System instruction for the agent
        model_name: Model to use (respects the model_name parameter)
        agent_name: Name for the agent
        
    Returns:
        Response text from the agent
    """
    try:
        # Create agent following core/*.py patterns
        agent = Agent(
            name=agent_name,
            model=LiteLlm(model=model_name),
            instruction=system_instruction
        )
        
        # Use established session management pattern
        session_service = InMemorySessionService()
        runner = Runner(
            app_name='AgentOptimizer',
            agent=agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            user_id='optimizer',
            session_id='generic_session',
            app_name='AgentOptimizer'
        )
        
        # Create message following types.Content pattern
        message = types.Content(role="user", parts=[{"text": prompt}])
        
        # Run agent following established pattern
        response_generator = runner.run(
            user_id='optimizer',
            session_id='generic_session',
            new_message=message
        )
        
        # Extract response following flexible_agents.py pattern
        response_text = ""
        for event in response_generator:
            if hasattr(event, 'content') and event.content:
                if event.is_final_response():
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error in generic LLM agent: {str(e)}")
        return ""