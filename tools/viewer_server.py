"""Agent-facing entrypoint for serving the Infra Error Archive Viewer."""

from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server" / "viewer_server.py"

runpy.run_path(str(SERVER), run_name="__main__")
