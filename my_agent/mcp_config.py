"""Load mcp_servers.json. For stdio servers, "python" becomes the current interpreter (your venv)
and relative .py paths are resolved against the repo root, so it works from any cwd."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_mcp_config(path: Path = ROOT / "mcp_servers.json") -> dict:
    config = json.loads(path.read_text())
    for server in config.values():
        if server.get("transport") != "stdio":
            continue
        if server.get("command") == "python":
            server["command"] = sys.executable
        server["args"] = [
            str(ROOT / a) if a.endswith(".py") and not Path(a).is_absolute() else a
            for a in server.get("args", [])
        ]
    return config
