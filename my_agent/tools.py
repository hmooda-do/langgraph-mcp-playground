"""Agent tools: local @tool functions + every MCP server available to this process.

MCP sources, merged into one tool list:
  1. mcp_servers.json  - your own servers (stdio demo server by default; add more).
  2. HARNESS_MCP_URL_* - set by MARS for each server declared under `tools:` in agents.yaml
                         (do.actions -> HARNESS_MCP_URL_DO_ACTIONS, inline server "foo" ->
                         HARNESS_MCP_URL_FOO). Plain streamable-HTTP MCP endpoints pinned to the
                         session; no credential needed here.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_core.tools import BaseTool, tool

from my_agent.mcp_bridge import load_tools
from my_agent.mcp_config import load_mcp_config

MARS_PREFIX = "HARNESS_MCP_URL_"


@tool
def current_utc_time() -> str:
    """Return the current date and time in UTC, in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


LOCAL_TOOLS: list[BaseTool] = [current_utc_time]


def mars_mcp_servers() -> dict:
    return {
        k[len(MARS_PREFIX):].lower(): {"url": v, "transport": "streamable_http"}
        for k, v in os.environ.items()
        if k.startswith(MARS_PREFIX) and v
    }


async def mcp_tools() -> list[BaseTool]:
    servers = {**load_mcp_config(), **mars_mcp_servers()}
    if not servers:
        return []
    tools: list[BaseTool] = []
    # Load per server so one unreachable server doesn't take the whole agent down.
    for name, cfg in servers.items():
        try:
            tools += await load_tools(cfg)
        except Exception as e:  # noqa: BLE001
            print(f"[tools] skipping MCP server {name!r}: {e}")
    return tools
