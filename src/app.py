"""
app.py - run the dashboard on your own computer

Usage:
    py src/app.py
    py src/app.py --port 9000
    py src/app.py --no-browser
"""
import argparse
import functools
import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):       # keep the terminal clean
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    if not (DOCS / "index.html").exists():
        raise SystemExit(f"Cannot find {DOCS / 'index.html'}. Put the dashboard file in the docs folder.")

    handler = functools.partial(QuietHandler, directory=str(DOCS))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler) as server:
        url = f"http://localhost:{args.port}"
        print(f"Dashboard running at {url}")
        print("Press Ctrl + C to stop.")
        if not args.no_browser:
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")