#!/usr/bin/env python3
"""Static Viewer server with a local API bridge to MCP-style tools."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
TOOL_SERVER = ROOT / "server" / "wiki_mcp_server.py"


class ViewerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path == "/":
            self.path = "/web/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/suggest-fix":
            self.handle_suggest_fix()
            return
        self.send_json({"error": "unknown endpoint"}, status=404)

    def handle_suggest_fix(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body) if body else {}
            message = str(payload.get("message", "")).strip()
            if not message:
                self.send_json({"error": "message is required"}, status=400)
                return

            result = subprocess.run(
                [sys.executable, str(TOOL_SERVER), "suggest-fix", message],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                self.send_json(
                    {
                        "error": "tool execution failed",
                        "stderr": (result.stderr or "").strip(),
                    },
                    status=500,
                )
                return
            stdout = (result.stdout or "").strip()
            if not stdout:
                self.send_json(
                    {
                        "error": "tool returned empty output",
                        "stderr": (result.stderr or "").strip(),
                    },
                    status=500,
                )
                return
            self.send_json(json.loads(stdout))
        except Exception as error:
            self.send_json({"error": str(error)}, status=500)

    def send_json(self, data: dict, status: int = 200) -> None:
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def translate_path(self, path: str) -> str:
        raw_path = unquote(path.split("?", 1)[0].split("#", 1)[0])
        requested_path = (ROOT / raw_path.lstrip("/")).resolve()
        try:
            requested_path.relative_to(ROOT)
        except ValueError:
            return str((ROOT / "web" / "index.html").resolve())
        return str(requested_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Infra Error Archive Viewer server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ViewerHandler)
    print(f"Serving Infra Error Archive at http://{args.host}:{args.port}/")
    print("API endpoint: POST /api/suggest-fix")
    server.serve_forever()


if __name__ == "__main__":
    main()
