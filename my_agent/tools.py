"""Agent tools: local @tool functions + every MCP server available to this process.

MCP sources, merged into one tool list:
  1. mcp_servers.json  - your own servers (stdio demo server by default; add more).
  2. HARNESS_MCP_URL_* - set by MARS for each server declared under `tools:` in agents.yaml
                         (do.actions -> HARNESS_MCP_URL_DO_ACTIONS, inline server "foo" ->
                         HARNESS_MCP_URL_FOO). Plain streamable-HTTP MCP endpoints pinned to the
                         session; no credential needed here.
"""
from __future__ import annotations

import asyncio
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


# Names containing these are treated as secrets: the tool reports "set" but never the value.
_SECRET_HINTS = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "AUTH", "COOKIE")
# Platform/system internals not worth listing.
_HIDE_PREFIXES = ("LS_", "LC_", "S6_", "OTEL_", "LANGSMITH_")


def _is_secret(name: str) -> bool:
    return any(h in name.upper() for h in _SECRET_HINTS)


@tool
def get_env(names: list[str]) -> dict:
    """Read environment variables of this agent runtime by exact name.

    Returns {name: value}. Secret-looking variables (KEY/SECRET/TOKEN/PASSWORD/...) are
    reported as "<redacted: set>" and never revealed; unset ones as null.
    """
    out = {}
    for n in names:
        v = os.environ.get(n)
        out[n] = None if v is None else ("<redacted: set>" if _is_secret(n) else v)
    return out


@tool
def list_env_names() -> list[str]:
    """List the names (not values) of environment variables available to this runtime."""
    return sorted(k for k in os.environ if not k.startswith(_HIDE_PREFIXES))


@tool
def get_runtime_info() -> dict:
    """Which model/endpoint this agent runs on, and which MCP servers MARS attached."""
    return {
        "model": os.getenv("HARNESS_INFERENCE_MODEL") or os.getenv("LLM_MODEL"),
        "inference_base_url": os.getenv("HARNESS_INFERENCE_BASE_URL"),
        "mars_mcp_servers": sorted(mars_mcp_servers()),
    }


LOCAL_TOOLS: list[BaseTool] = [current_utc_time, get_env, list_env_names, get_runtime_info]


def mars_mcp_servers() -> dict:
    return {
        k[len(MARS_PREFIX):].lower(): {"url": v, "transport": "streamable_http"}
        for k, v in os.environ.items()
        if k.startswith(MARS_PREFIX) and v
    }


async def mcp_tools() -> tuple[list[BaseTool], list[str]]:
    """Load tools from every MCP server. Returns (tools, names of servers that failed).

    Each server gets a few attempts: on MARS the Action Gateway endpoint can lag the
    Agent Server's start, and a single failed attempt must not leave the agent tool-less.
    """
    servers = {**load_mcp_config(), **mars_mcp_servers()}
    tools: list[BaseTool] = []
    failed: list[str] = []
    for name, cfg in servers.items():
        for attempt in range(1, 4):
            try:
                loaded = await load_tools(cfg)
                print(f"[tools] MCP server {name!r}: {len(loaded)} tools")
                tools += loaded
                break
            except Exception as e:  # noqa: BLE001
                print(f"[tools] MCP server {name!r} attempt {attempt}/3 failed: {e!r}")
                if attempt == 3:
                    failed.append(name)
                else:
                    await asyncio.sleep(2 * attempt)
    return tools, failed
