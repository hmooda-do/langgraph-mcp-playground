"""Run one turn of the MCP agent locally (no Agent Server).

Usage: python examples/02_mcp_agent.py "What is 17.5 + 24.25, and what time is it in UTC?"
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from my_agent.agent import make_graph


async def main(question: str) -> None:
    graph = await make_graph()
    result = await graph.ainvoke({"messages": [("user", question)]})
    for m in result["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What is 17.5 + 24.25, and what time is it in UTC?"))
