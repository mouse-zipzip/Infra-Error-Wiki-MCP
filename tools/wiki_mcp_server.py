"""Agent-facing entrypoint for the Infra Error Archive MCP-style tools.

This wrapper keeps the tool surface under tools/ for external agents while
reusing the implementation in server/wiki_mcp_server.py.
"""

from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server" / "wiki_mcp_server.py"

runpy.run_path(str(SERVER), run_name="__main__")
