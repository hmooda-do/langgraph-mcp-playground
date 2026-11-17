"""Minimal MCP -> LangChain tool bridge built on the `mcp` SDK.

Why not langchain-mcp-adapters? It pins mcp<2 while the LangGraph Agent Server
(langgraph-api, preinstalled on MARS) needs mcp>=2.3, so installing it would downgrade mcp
underneath the server. This bridge only needs `mcp` itself.

Each tool call opens its own short-lived MCP session, so nothing stays connected.
Transports: "stdio" and "streamable_http".
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool, StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client


@asynccontextmanager
async def _session(cfg: dict):
    transport = cfg.get("transport", "streamable_http")
    if transport == "stdio":
        params = StdioServerParameters(command=cfg["command"], args=cfg.get("args", []), env=cfg.get("env"))
        cm = stdio_client(params)
    elif transport == "streamable_http":
        cm = streamable_http_client(cfg["url"])
    else:
        raise ValueError(f"unsupported MCP transport {transport!r} (use stdio or streamable_http)")
    async with cm as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


def _text(result) -> str:
    parts = [getattr(c, "text", None) or str(c) for c in result.content]
    out = "\n".join(parts)
    if getattr(result, "is_error", False):
        raise RuntimeError(out or "MCP tool returned an error")
    return out


def _make_tool(cfg: dict, name: str, description: str, schema: dict) -> BaseTool:
    async def call(**kwargs) -> str:
        async with _session(cfg) as s:
            return _text(await s.call_tool(name, kwargs))

    return StructuredTool(name=name, description=description or name, args_schema=schema, coroutine=call)


async def load_tools(cfg: dict) -> list[BaseTool]:
    async with _session(cfg) as s:
        listed = await s.list_tools()
    return [_make_tool(cfg, t.name, t.description or "", t.input_schema) for t in listed.tools]
