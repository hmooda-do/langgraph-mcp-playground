# langgraph-mcp-playground

A LangGraph ReAct agent that runs **locally** and on **DigitalOcean Managed Agents (MARS)**, with an LLM and MCP tools.

MARS clones this repo at a pinned commit, runs `pip install -r requirements.txt`, and serves the graph in
`langgraph.json` with `langgraph dev`. (A `langgraph.json` at the repo root with exactly one graph is required.)

```
langgraph.json       # one graph: agent -> my_agent/agent.py:make_graph
requirements.txt     # installed by MARS at boot
agents.yaml          # MARS agent spec (model, secrets, MCP tools, permissions)
my_agent/
  agent.py           # ReAct loop (agent <-> tools)
  llm.py             # model factory (HARNESS_INFERENCE_* on MARS; or LLM_PROVIDER locally)
  tools.py           # local tools + all MCP servers
  mcp_bridge.py      # MCP -> LangChain tools (built on the `mcp` SDK)
mcp_servers.json     # your own MCP servers (local demo server by default)
servers/demo_server.py
scripts/pin_commit.py
examples/            # 01 basic two-node graph, 02 one-shot MCP agent turn
```

## Run on MARS

```bash
git push && python scripts/pin_commit.py      # writes repo + HEAD sha into agents.yaml
doctl agents start agents.yaml ...            # see `doctl agents start --help`; the key is a tenant secret:
#   --secret HARNESS_INFERENCE_API_KEY=@$HOME/.inference_key
```

Tools via MARS: list them under `tools:` in `agents.yaml`. MARS exposes each server's URL as
`HARNESS_MCP_URL_<NAME>` (`do.actions` -> `HARNESS_MCP_URL_DO_ACTIONS`) and `my_agent/tools.py` loads every
such variable automatically. Use `do.actions: [...]` for the managed Action Gateway catalog, or an inline
`{name, url, auth}` entry for any remote https MCP server. Control access with `permissions:`.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt "langgraph-cli[inmem]"
cp .env.example .env        # set HARNESS_INFERENCE_* (any OpenAI-compatible endpoint) or LLM_PROVIDER + key
python examples/02_mcp_agent.py "What is 17.5 + 24.25, and what time is it in UTC?"
langgraph dev               # same Agent Server MARS runs, with Studio
```

## MCP servers

- **MARS-managed:** `tools:` in `agents.yaml` (above).
- **Your own:** add to `mcp_servers.json` (`stdio` or `streamable_http`). Local stdio servers run in the sandbox too.
  Remote servers needing a token should use an inline `tools:` entry with `auth.secret` on MARS instead.

> `langchain-mcp-adapters` is intentionally not used: it pins `mcp<2`, but the Agent Server needs `mcp>=2.3`.
