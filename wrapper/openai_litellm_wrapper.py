#!/usr/bin/env python3
"""
OpenAI LiteLLM Wrapper for Google ADK Agents

This module provides a wrapper class that accepts an openai.OpenAI client
and functions as a LiteLLM model compatible with Google ADK agents.
"""

import json
from typing import Any, Dict, List, AsyncGenerator
from openai import OpenAI
from pydantic import Field
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import types
Content = types.Content
Part = types.Part


class OpenAILiteLLMWrapper(BaseLlm):
    """
    A wrapper class that makes an OpenAI client compatible with Google ADK's LiteLLM interface.
    
    This allows you to use an existing OpenAI client instance with Google ADK agents
    while maintaining the standard LiteLLM model interface.
    """
    
    # Define additional fields that are not in the parent class
    client: OpenAI = Field(default=None, exclude=True)
    temperature: float = Field(default=0.7, exclude=True)
    max_tokens: int = Field(default=1000, exclude=True)
    
    def __init__(
        self, 
        openai_client: OpenAI,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Initialize the wrapper with an OpenAI client.
        
        Args:
            openai_client: An initialized openai.OpenAI client instance
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
            client=openai_client,
            temperature=temperature,
            max_tokens=max_tokens,
            **clean_kwargs
        )
        self._additional_args = clean_kwargs
    
    def _convert_content_to_openai_message(self, content: Content) -> Dict[str, Any]:
        """
        Convert Google ADK Content to a single OpenAI message.
        
        Args:
            content: Google ADK Content object
            
        Returns:
            OpenAI message dictionary or None
        """
        if hasattr(content, 'parts') and content.parts:
            text_parts = []
            function_calls = []
            function_responses = []
            
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
                elif hasattr(part, 'function_call') and part.function_call:
                    # Handle function call - convert args dict to JSON string
                    args_str = part.function_call.args
                    if isinstance(args_str, dict):
                        args_str = json.dumps(args_str)
                    elif args_str is None:
                        args_str = "{}"
                    
                    function_calls.append({
                        "id": getattr(part.function_call, 'id', 'call_1'),
                        "type": "function", 
                        "function": {
                            "name": part.function_call.name,
                            "arguments": args_str
                        }
                    })
                elif hasattr(part, 'function_response') and part.function_response:
                    # Handle function response
                    function_responses.append(part.function_response)
            
            role = getattr(content, 'role', 'user')
            
            if function_calls:
                # Assistant message with tool calls
                return {
                    "role": "assistant",
                    "content": "\n".join(text_parts) if text_parts else None,
                    "tool_calls": function_calls
                }
            elif function_responses:
                # Tool response message
                return {
                    "role": "tool",
                    "content": str(function_responses[0].response) if function_responses else "",
                    "tool_call_id": getattr(function_responses[0], 'id', 'call_1') if function_responses else 'call_1'
                }
            elif text_parts:
                # Regular text message
                return {
                    "role": role,
                    "content": "\n".join(text_parts)
                }
        
        return None

    def _convert_content_to_messages(self, content: Content) -> List[Dict[str, Any]]:
        """
        Convert Google ADK Content to OpenAI messages format.
        
        Args:
            content: Google ADK Content object
            
        Returns:
            List of message dictionaries in OpenAI format
        """
        messages = []
        
        if hasattr(content, 'parts') and content.parts:
            # Handle multi-part content
            text_parts = []
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if text_parts:
                combined_text = "\n".join(text_parts)
                messages.append({
                    "role": getattr(content, 'role', 'user'),
                    "content": combined_text
                })
        elif hasattr(content, 'text'):
            # Handle simple text content
            messages.append({
                "role": getattr(content, 'role', 'user'),
                "content": content.text
            })
        
        return messages
    
    def _create_content_response(self, text: str, role: str = "assistant") -> Content:
        """
        Create a Google ADK Content response from text.
        
        Args:
            text: The response text
            role: The role for the response (default: assistant)
            
        Returns:
            Google ADK Content object
        """
        return Content(
            role=role,
            parts=[Part(text=text)]
        )

    def _convert_function_declaration_to_openai_tool(self, func_decl) -> Dict[str, Any]:
        """
        Convert Google ADK function declaration to OpenAI tool format.
        
        Args:
            func_decl: Google ADK function declaration
            
        Returns:
            OpenAI tool dictionary
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
                            # Default fallback
                            prop_def["type"] = "string"
                    
                    # Add description if available and not None
                    if hasattr(prop_schema, 'description') and prop_schema.description:
                        prop_def["description"] = prop_schema.description
                    
                    # Add enum if available (but skip default values)
                    if hasattr(prop_schema, 'enum') and prop_schema.enum:
                        prop_def["enum"] = prop_schema.enum
                    
                    # Note: We explicitly skip default values as they're not supported in Google AI
                    
                    tool["function"]["parameters"]["properties"][prop_name] = prop_def
                
                # Add required fields
                if hasattr(func_decl.parameters, 'required'):
                    tool["function"]["parameters"]["required"] = func_decl.parameters.required
            else:
                # If no properties, check if the parameters object itself has type info
                if hasattr(func_decl.parameters, 'type'):
                    tool["function"]["parameters"]["type"] = func_decl.parameters.type.lower()
        
        return tool
    
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generate content asynchronously using the OpenAI client.
        
        Args:
            llm_request: The LLM request containing messages and parameters
            stream: Whether to stream the response
            
        Yields:
            LlmResponse objects with the generated content
        """
        # Ensure proper user content is appended (following BaseLlm pattern)
        self._maybe_append_user_content(llm_request)

        # Convert LlmRequest to OpenAI messages format
        messages = []
        
        # Process the content from the LlmRequest
        if hasattr(llm_request, 'contents') and llm_request.contents:
            for content in llm_request.contents:
                message = self._convert_content_to_openai_message(content)
                if message:
                    messages.append(message)
        
        # Add system instruction if available
        if (hasattr(llm_request, 'config') and llm_request.config and 
            hasattr(llm_request.config, 'system_instruction') and 
            llm_request.config.system_instruction):
            messages.insert(0, {
                "role": "system",
                "content": llm_request.config.system_instruction
            })
        elif not any(msg.get('role') == 'system' for msg in messages):
            # Fallback system message
            messages.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant."
            })
        
        # Extract tools from the request
        tools = None
        if (hasattr(llm_request, 'config') and llm_request.config and 
            hasattr(llm_request.config, 'tools') and llm_request.config.tools and
            len(llm_request.config.tools) > 0 and 
            hasattr(llm_request.config.tools[0], 'function_declarations') and
            llm_request.config.tools[0].function_declarations):
            
            tools = []
            for func_decl in llm_request.config.tools[0].function_declarations:
                tool = self._convert_function_declaration_to_openai_tool(func_decl)
                if tool:
                    tools.append(tool)
        
        # Merge instance parameters
        generation_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Add tools if available
        if tools:
            generation_params["tools"] = tools
        
        # Add streaming if requested
        if stream:
            generation_params["stream"] = True
        
        try:
            if stream:
                # Handle streaming response
                stream_response = self.client.chat.completions.create(**generation_params)
                full_text = ""
                function_calls = {}  # Track function calls by ID
                
                for chunk in stream_response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        
                        # Handle text content
                        if delta.content:
                            chunk_text = delta.content
                            full_text += chunk_text
                            
                            # Create partial response for streaming
                            llm_response = LlmResponse(
                                content=Content(
                                    role="assistant",
                                    parts=[Part(text=chunk_text)]
                                )
                            )
                            yield llm_response
                        
                        # Handle function calls in streaming
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                if tool_call.type == "function":
                                    call_id = tool_call.id
                                    if call_id not in function_calls:
                                        function_calls[call_id] = {
                                            "name": "",
                                            "arguments": "",
                                            "id": call_id
                                        }
                                    
                                    if tool_call.function.name:
                                        function_calls[call_id]["name"] += tool_call.function.name
                                    if tool_call.function.arguments:
                                        function_calls[call_id]["arguments"] += tool_call.function.arguments
                
                # Send final response with complete function calls if any
                final_parts = []
                if full_text:
                    final_parts.append(Part(text=full_text))
                
                for call_data in function_calls.values():
                    if call_data["name"]:  # Only add if we have a complete function call
                        # Parse arguments string to dict if needed
                        try:
                            args_dict = json.loads(call_data["arguments"]) if call_data["arguments"] else {}
                        except json.JSONDecodeError:
                            args_dict = {}
                        
                        func_call_part = Part(
                            function_call=types.FunctionCall(
                                name=call_data["name"],
                                args=args_dict,
                                id=call_data["id"]
                            )
                        )
                        final_parts.append(func_call_part)
                
                if final_parts:
                    final_response = LlmResponse(
                        content=Content(
                            role="assistant",
                            parts=final_parts
                        )
                    )
                    yield final_response
            else:
                # Handle non-streaming response
                response = self.client.chat.completions.create(**generation_params)
                message = response.choices[0].message
                
                # Convert OpenAI response to Google ADK format
                content_parts = []
                
                # Add text content if present
                if message.content:
                    content_parts.append(Part(text=message.content))
                
                # Add function calls if present
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call.type == "function":
                            # Parse arguments string to dict if needed
                            try:
                                args_dict = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                            except json.JSONDecodeError:
                                args_dict = {}
                            
                            func_call_part = Part(
                                function_call=types.FunctionCall(
                                    name=tool_call.function.name,
                                    args=args_dict,
                                    id=tool_call.id
                                )
                            )
                            content_parts.append(func_call_part)
                
                # Ensure we have at least some content
                if not content_parts:
                    content_parts = [Part(text="")]
                
                llm_response = LlmResponse(
                    content=Content(
                        role="assistant",
                        parts=content_parts
                    )
                )
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
    


def create_openai_litellm_wrapper(
    openai_client: OpenAI,
    model: str = "gpt-4o",
    **kwargs
) -> OpenAILiteLLMWrapper:
    """
    Factory function to create an OpenAI LiteLLM wrapper.
    
    Args:
        openai_client: An initialized openai.OpenAI client instance
        model: The model name to use (default: gpt-4o)
        **kwargs: Additional parameters for the wrapper
        
    Returns:
        OpenAILiteLLMWrapper instance
    """
    return OpenAILiteLLMWrapper(
        openai_client=openai_client,
        model=model,
        **kwargs
    )