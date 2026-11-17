"""ReAct agent for LangGraph / MARS: START -> agent -> (tool calls?) -> tools -> agent -> END.

Standard LangGraph, no platform-specific imports. MARS clones the repo, installs
requirements.txt and serves the graph in langgraph.json with `langgraph dev`.
No `from __future__ import annotations` here: LangGraph reads the state annotations at runtime.
"""
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from my_agent.llm import get_llm
from my_agent.tools import LOCAL_TOOLS, mcp_tools

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use your tools when they help you answer accurately, "
    "and say so when you are unsure."
)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # MARS streams the last AI message as the reply


def build_graph(tools: list):
    model = get_llm().bind_tools(tools) if tools else get_llm()

    def agent(state: AgentState) -> dict:
        return {"messages": [model.invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])]}

    wf = StateGraph(AgentState)
    wf.add_node("agent", agent)
    wf.add_edge(START, "agent")
    if tools:
        wf.add_node("tools", ToolNode(tools))
        wf.add_conditional_edges("agent", tools_condition)
        wf.add_edge("tools", "agent")
    else:
        wf.add_edge("agent", END)
    return wf.compile()


_graph = None


async def make_graph():
    """Factory named in langgraph.json. Built once: a session's tool set doesn't change mid-run."""
    global _graph
    if _graph is None:
        _graph = build_graph([*LOCAL_TOOLS, *await mcp_tools()])
    return _graph
