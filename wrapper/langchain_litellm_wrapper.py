#!/usr/bin/env python3
"""
LangChain LiteLLM Wrapper for Google ADK Agents

This module provides a wrapper class that accepts a LangChain chat model
and functions as a LiteLLM model compatible with Google ADK agents.
"""

import json
from typing import Any, Dict, List, AsyncGenerator
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from pydantic import Field
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import types
Content = types.Content
Part = types.Part


class LangChainLiteLLMWrapper(BaseLlm):
    """
    A wrapper class that makes a LangChain chat model compatible with Google ADK's LiteLLM interface.
    
    This allows you to use an existing LangChain chat model instance with Google ADK agents
    while maintaining the standard LiteLLM model interface.
    """
    
    # Define additional fields that are not in the parent class
    langchain_model: BaseChatModel = Field(default=None, exclude=True)
    temperature: float = Field(default=0.7, exclude=True)
    max_tokens: int = Field(default=1000, exclude=True)
    
    def __init__(
        self, 
        langchain_model: BaseChatModel,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Initialize the wrapper with a LangChain chat model.
        
        Args:
            langchain_model: An initialized LangChain chat model instance
            model: The model name to use (default: gpt-4o)
            temperature: Temperature for response generation (default: 0.7)
            max_tokens: Maximum tokens in response (default: 1000)
            **kwargs: Additional parameters passed to the base class
        """
        # Remove conflicting parameters before passing to parent
        clean_kwargs = kwargs.copy()
        clean_kwargs.pop("llm_client", None)
        clean_kwargs.pop("messages", None)
        clean_kwargs.pop("tools", None)
        clean_kwargs.pop("stream", None)
        
        super().__init__(
            model=model, 
            client=langchain_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **clean_kwargs
        )
        
        # Store the LangChain model instance
        self.langchain_model = langchain_model
        self._additional_args = clean_kwargs
    
    def _convert_content_to_langchain_message(self, content: Content) -> BaseMessage:
        """
        Convert Google ADK Content to LangChain message format.
        
        Args:
            content: Google ADK Content object
            
        Returns:
            LangChain BaseMessage object
        """
        if hasattr(content, 'parts') and content.parts:
            text_parts = []
            tool_calls = []
            
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
                elif hasattr(part, 'function_call') and part.function_call:
                    # Handle function call
                    args_dict = part.function_call.args
                    if isinstance(args_dict, str):
                        try:
                            args_dict = json.loads(args_dict)
                        except json.JSONDecodeError:
                            args_dict = {}
                    elif args_dict is None:
                        args_dict = {}
                    
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": args_dict,
                        "id": getattr(part.function_call, 'id', 'call_1')
                    })
                elif hasattr(part, 'function_response') and part.function_response:
                    # Handle function response - create a ToolMessage
                    return ToolMessage(
                        content=str(part.function_response.response),
                        tool_call_id=getattr(part.function_response, 'id', 'call_1')
                    )
            
            role = getattr(content, 'role', 'user')
            combined_text = "\n".join(text_parts) if text_parts else ""
            
            if role == 'system':
                return SystemMessage(content=combined_text)
            elif role == 'assistant':
                if tool_calls:
                    return AIMessage(content=combined_text, tool_calls=tool_calls)
                else:
                    return AIMessage(content=combined_text)
            else:  # user or other roles
                return HumanMessage(content=combined_text)
        
        # Fallback for simple content
        role = getattr(content, 'role', 'user')
        text = getattr(content, 'text', '')
        
        if role == 'system':
            return SystemMessage(content=text)
        elif role == 'assistant':
            return AIMessage(content=text)
        else:
            return HumanMessage(content=text)
    
    def _convert_content_to_langchain_messages(self, content: Content) -> List[BaseMessage]:
        """
        Convert Google ADK Content to LangChain messages format.
        
        Args:
            content: Google ADK Content object
            
        Returns:
            List of LangChain BaseMessage objects
        """
        message = self._convert_content_to_langchain_message(content)
        return [message] if message else []
    
    def _create_content_response(self, message: BaseMessage) -> Content:
        """
        Create a Google ADK Content response from a LangChain message.
        
        Args:
            message: The LangChain message
            
        Returns:
            Google ADK Content object
        """
        parts = []
        
        # Handle text content
        if hasattr(message, 'content') and message.content:
            parts.append(Part(text=message.content))
        
        # Handle tool calls if present
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                func_call_part = Part(
                    function_call=types.FunctionCall(
                        name=tool_call["name"],
                        args=tool_call["args"],
                        id=tool_call.get("id", "call_1")
                    )
                )
                parts.append(func_call_part)
        
        # Ensure we have at least some content
        if not parts:
            parts = [Part(text="")]
        
        return Content(
            role="assistant",
            parts=parts
        )

    def _convert_function_declaration_to_langchain_tool(self, func_decl) -> Dict[str, Any]:
        """
        Convert Google ADK function declaration to LangChain tool format.
        
        Args:
            func_decl: Google ADK function declaration
            
        Returns:
            LangChain tool dictionary
        """
        tool = {
            "type": "function",
            "function": {
                "name": func_decl.name,
                "description": getattr(func_decl, 'description', ''),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # Convert parameters if they exist
        if hasattr(func_decl, 'parameters') and func_decl.parameters:
            # Handle Google ADK schema format
            if hasattr(func_decl.parameters, 'properties'):
                for prop_name, prop_schema in func_decl.parameters.properties.items():
                    prop_def = {}
                    
                    # Convert Google ADK types to JSON Schema types
                    if hasattr(prop_schema, 'type'):
                        gdk_type = prop_schema.type
                        if gdk_type == 'STRING':
                            prop_def["type"] = "string"
                        elif gdk_type == 'INTEGER':
                            prop_def["type"] = "integer"
                        elif gdk_type == 'NUMBER':
                            prop_def["type"] = "number"
                        elif gdk_type == 'BOOLEAN':
                            prop_def["type"] = "boolean"
                        elif gdk_type == 'ARRAY':
                            prop_def["type"] = "array"
                        elif gdk_type == 'OBJECT':
                            prop_def["type"] = "object"
                        else:
                            prop_def["type"] = "string"
                    
                    # Add description if available
                    if hasattr(prop_schema, 'description') and prop_schema.description:
                        prop_def["description"] = prop_schema.description
                    
                    # Add enum if available
                    if hasattr(prop_schema, 'enum') and prop_schema.enum:
                        prop_def["enum"] = prop_schema.enum
                    
                    tool["function"]["parameters"]["properties"][prop_name] = prop_def
                
                # Add required fields
                if hasattr(func_decl.parameters, 'required'):
                    tool["function"]["parameters"]["required"] = func_decl.parameters.required
        
        return tool
    
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generate content asynchronously using the LangChain model.
        
        Args:
            llm_request: The LLM request containing messages and parameters
            stream: Whether to stream the response (Note: LangChain streaming may vary by model)
            
        Yields:
            LlmResponse objects with the generated content
        """
        # Ensure proper user content is appended (following BaseLlm pattern)
        self._maybe_append_user_content(llm_request)
        
        # Convert LlmRequest to LangChain messages format
        messages = []
        
        # Add system instruction if available
        if (hasattr(llm_request, 'config') and llm_request.config and 
            hasattr(llm_request.config, 'system_instruction') and 
            llm_request.config.system_instruction):
            messages.append(SystemMessage(content=llm_request.config.system_instruction))
        
        # Process the content from the LlmRequest
        if hasattr(llm_request, 'contents') and llm_request.contents:
            for content in llm_request.contents:
                langchain_messages = self._convert_content_to_langchain_messages(content)
                messages.extend(langchain_messages)
        
        # Extract tools from the request and bind them to the model if available
        langchain_model = self.langchain_model
        if (hasattr(llm_request, 'config') and llm_request.config and 
            hasattr(llm_request.config, 'tools') and llm_request.config.tools and
            len(llm_request.config.tools) > 0 and 
            hasattr(llm_request.config.tools[0], 'function_declarations') and
            llm_request.config.tools[0].function_declarations):
            
            tools = []
            for func_decl in llm_request.config.tools[0].function_declarations:
                tool = self._convert_function_declaration_to_langchain_tool(func_decl)
                if tool:
                    tools.append(tool)
            
            # Try to bind tools to the model if it supports it
            if hasattr(langchain_model, 'bind_tools') and tools:
                langchain_model = langchain_model.bind_tools(tools)
        
        try:
            if stream and hasattr(langchain_model, 'astream'):
                # Handle streaming response if supported
                full_content = ""
                async for chunk in langchain_model.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        chunk_text = chunk.content
                        full_content += chunk_text
                        
                        # Create partial response for streaming
                        llm_response = LlmResponse(
                            content=Content(
                                role="assistant",
                                parts=[Part(text=chunk_text)]
                            )
                        )
                        yield llm_response
                
                # Send final complete response if we have tool calls or need to finalize
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    final_content = self._create_content_response(chunk)
                    final_response = LlmResponse(content=final_content)
                    yield final_response
            else:
                # Handle non-streaming response
                if hasattr(langchain_model, 'ainvoke'):
                    response = await langchain_model.ainvoke(messages)
                else:
                    # Fallback to synchronous invoke
                    response = langchain_model.invoke(messages)
                
                # Convert LangChain response to Google ADK format
                content = self._create_content_response(response)
                llm_response = LlmResponse(content=content)
                yield llm_response
                
        except Exception as e:
            error_text = f"Error generating content: {str(e)}"
            error_response = LlmResponse(
                content=Content(
                    role="assistant",
                    parts=[Part(text=error_text)]
                )
            )
            yield error_response


def create_langchain_litellm_wrapper(
    langchain_model: BaseChatModel,
    model: str = "gpt-4o",
    **kwargs
) -> LangChainLiteLLMWrapper:
    """
    Factory function to create a LangChain LiteLLM wrapper.
    
    Args:
        langchain_model: An initialized LangChain chat model instance
        model: The model name to use (default: gpt-4o)
        **kwargs: Additional parameters for the wrapper
        
    Returns:
        LangChainLiteLLMWrapper instance
    """
    return LangChainLiteLLMWrapper(
        langchain_model=langchain_model,
        model=model,
        **kwargs
    )