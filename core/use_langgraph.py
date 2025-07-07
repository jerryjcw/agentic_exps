import os
import sys
import json
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableLambda
from langgraph.graph import START, END, StateGraph
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from gpt_caller import get_api_key
from typing import Annotated

from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


class MySpecialAdditionInput(BaseModel):
    a: int = Field(..., description="The first integer to add.")
    b: int = Field(..., description="The second integer to add.")


@tool("my_special_addition_tool", args_schema=MySpecialAdditionInput, return_direct=True)
def my_special_addition(a: int, b: int) -> int:
    """
    Adds two integers together in a special way called "my special addition", it does not apply to usual addition..
    Args:
        a (int): The first integer.
        b (int): The second integer.
    Returns:
        int: My special addition result of the two integers.
    """
    return (a + b) * 2


def route_tools(state: State):
    if isinstance(state, list):
        message = state[-1]
    elif messages := state.get("messages", []):
        message = messages[-1]
    else:
        raise ValueError("No messages found in state.")
    if hasattr(message, 'tool_calls') and message.tool_calls:
        return "tools"
    return END


class BasicToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


graph_builder = StateGraph(State)  # Initialize the graph builder

tools = [my_special_addition]

os.environ["OPENAI_API_KEY"] = get_api_key(file_path=sys.argv[1])  # Set your OpenAI API key
llm = init_chat_model("openai:gpt-4o")
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

tool_node = BasicToolNode(tools)
llm_with_tools = llm.bind_tools(tools)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {
        "tools": "tools",  # If tools are called, go to the tools node
        END: END,          # If no tools are called, end the graph
    }
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            print("Please ask a question or type 'quit' to exit.")

