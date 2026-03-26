#!/usr/bin/env python3
import argparse
import os
import socket
import subprocess
import sys
import threading
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class TrendStageHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/") == "/__shutdown":
            # Only allow shutdown from the local machine.
            client_ip = (self.client_address[0] or "").strip()
            if client_ip not in ("127.0.0.1", "::1"):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"forbidden")
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"shutting down")

            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        return super().do_POST()


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _run_pipeline(repo_root: Path, env: dict, quiet: bool) -> int:
    pipeline_dir = repo_root / "pundit_pipeline" / "pipeline"
    pipeline_entry = pipeline_dir / "run_pipeline_v2.py"
    if not pipeline_entry.exists():
        print(f"[start] Missing pipeline entry: {pipeline_entry}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(pipeline_entry)]
    stdout = subprocess.DEVNULL if quiet else None
    stderr = subprocess.STDOUT if quiet else None
    print("[start] Running pipeline…")
    proc = subprocess.run(cmd, cwd=str(pipeline_dir), env=env, stdout=stdout, stderr=stderr)
    if proc.returncode != 0:
        print(f"[start] Pipeline failed with exit code {proc.returncode}", file=sys.stderr)
    else:
        print("[start] Pipeline complete.")
    return proc.returncode


def _port_available(host: str, port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
        return True


def _serve_webapp(repo_root: Path, host: str, port: int):
    webapp_dir = repo_root / "webapp"
    if not webapp_dir.exists():
        print(f"[start] Missing webapp dir: {webapp_dir}", file=sys.stderr)
        return 1

    if not _port_available(host, port):
        print(f"[start] Port in use: {host}:{port}", file=sys.stderr)
        print(f"[start] If you already started the server, open: http://localhost:{port}/index.html")
        return 2

    os.chdir(str(webapp_dir))
    httpd = ThreadingHTTPServer((host, port), TrendStageHandler)
    url = f"http://localhost:{port}/index.html"
    print(f"[start] Serving webapp from {webapp_dir}")
    print(f"[start] Open: {url}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the full pipeline and serve the webapp locally."
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--no-pipeline", action="store_true")
    parser.add_argument("--no-server", action="store_true")
    parser.add_argument("--quiet-pipeline", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root()
    topics_path = repo_root / "webapp" / "topics"

    env = dict(os.environ)
    env.setdefault("TRENDSTAGE_TOPICS_PATH", str(topics_path))

    if not args.no_pipeline:
        code = _run_pipeline(repo_root, env=env, quiet=args.quiet_pipeline)
        if code != 0:
            return code

    if args.no_server:
        print("[start] Done (server disabled).")
        return 0

    return _serve_webapp(repo_root, host=args.host, port=args.port)


if __name__ == "__main__":
    raise SystemExit(main())
