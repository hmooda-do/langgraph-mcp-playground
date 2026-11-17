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
from my_agent.tools import LOCAL_TOOLS, mars_mcp_servers, mcp_tools

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use your tools when they help you answer accurately, "
    "and say so when you are unsure. You have MCP tools: for GitHub and other external services, "
    "use action_search to find a tool and action_invoke to run it (if those are present), or call "
    "the tools you are given directly. Never claim a tool is unavailable without checking your tool list."
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
_graph_key = None


async def make_graph():
    """Factory named in langgraph.json; the Agent Server calls it on every run.

    The graph is cached only when every MCP server loaded and the MARS tool env is unchanged.
    A failed or late MCP server is retried on the next run instead of being cached as "no tools".
    """
    global _graph, _graph_key
    key = tuple(sorted(mars_mcp_servers().items(), key=lambda kv: kv[0]))
    key = tuple((k, v["url"]) for k, v in key)
    if _graph is not None and _graph_key == key:
        return _graph
    tools, failed = await mcp_tools()
    graph = build_graph([*LOCAL_TOOLS, *tools])
    if not failed:
        _graph, _graph_key = graph, key
    return graph
