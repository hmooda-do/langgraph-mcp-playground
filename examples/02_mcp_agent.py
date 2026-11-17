"""ReAct agent whose tools come from the MCP servers listed in mcp_servers.json.

Usage: python examples/02_mcp_agent.py "What is 17.5 + 24.25, and what time is it in UTC?"
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from llm import get_llm
from mcp_config import load_mcp_config


async def main(question: str) -> None:
    client = MultiServerMCPClient(load_mcp_config())
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}\n")

    agent = create_react_agent(get_llm(), tools)
    result = await agent.ainvoke({"messages": [("user", question)]})

    for m in result["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is 17.5 + 24.25, and what time is it in UTC?"
    asyncio.run(main(q))
