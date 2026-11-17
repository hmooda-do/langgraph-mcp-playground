# langgraph-mcp-playground

Minimal [LangGraph](https://langchain-ai.github.io/langgraph/) starter for two experiments:

1. **Connect an LLM** and do basic work (`examples/01_basic_graph.py`)
2. **Connect MCP servers** and let an agent use their tools (`examples/02_mcp_agent.py`)

## Setup

```bash
git clone <this-repo-url> && cd langgraph-mcp-playground
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # add your API key
```

## 1. LLM

`llm.py` is the only place the model is chosen. Set in `.env`:

| Goal | Settings |
|---|---|
| Anthropic | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY` |
| OpenAI | `LLM_PROVIDER=openai`, `OPENAI_API_KEY` |
| Any OpenAI-compatible endpoint (DO Inference, vLLM, Ollama, LiteLLM) | `LLM_PROVIDER=openai`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL` |

```bash
python examples/01_basic_graph.py "Some text to summarize"
```

## 2. MCP

Servers are declared in `mcp_servers.json`. A local demo server (`servers/demo_server.py`: `add`, `utc_now`, `word_count`) works out of the box:

```bash
python examples/02_mcp_agent.py "What is 17.5 + 24.25, and what time is it in UTC?"
```

Add your own servers to `mcp_servers.json`:

```json
{
  "demo":   { "transport": "stdio", "command": "python", "args": ["servers/demo_server.py"] },
  "fs":     { "transport": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/some/dir"] },
  "remote": { "transport": "streamable_http", "url": "https://example.com/mcp",
              "headers": { "Authorization": "Bearer <token>" } }
}
```

Transports: `stdio`, `streamable_http`, `sse`. Tools from all servers are merged into one agent.

## Layout

```
llm.py            model factory
mcp_config.py     mcp_servers.json loader
mcp_servers.json  MCP servers to connect
servers/          local demo MCP server
examples/         01 basic graph, 02 MCP ReAct agent
```
