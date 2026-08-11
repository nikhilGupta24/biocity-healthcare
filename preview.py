#!/usr/bin/env python3
"""
Biocity — local preview launcher.

Serves this folder over HTTP and opens the zoomable design board in your
browser. Running over HTTP (not file://) is what lets the live site load
inside the board's frames with correct theming.

    python3 preview.py                 # open the design board
    python3 preview.py --site          # open the actual v3 site instead
    python3 preview.py --port 8100      # pick a port (default 8099)

Ctrl-C to stop.
"""
import os
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))


def _port():
    argv = sys.argv[1:]
    if "--port" in argv:
        i = argv.index("--port")
        if i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                pass
    for a in argv:
        if a.startswith("--port="):
            try:
                return int(a.split("=", 1)[1])
            except ValueError:
                pass
    return 8099


def main():
    port = _port()
    target = "v3/index.html" if "--site" in sys.argv[1:] else "design-board.html"
    handler = partial(SimpleHTTPRequestHandler, directory=ROOT)
    handler.log_message = lambda *a, **k: None
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/{target}"
    print(f"Serving Biocity at http://127.0.0.1:{port}/")
    print(f"Opening {url}")
    print("Press Ctrl-C to stop.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
