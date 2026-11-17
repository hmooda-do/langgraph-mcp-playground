"""Tiny local MCP server (stdio) so you can test MCP without any external service."""
from datetime import datetime, timezone

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("demo")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def utc_now() -> str:
    """Current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


if __name__ == "__main__":
    mcp.run(transport="stdio")
