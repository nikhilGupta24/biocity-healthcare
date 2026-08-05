#!/usr/bin/env bash
# Serve the mirrored Biocity v3 site locally.
# Usage: ./serve.sh [PORT]   (default 8090)
set -euo pipefail

PORT="${1:-8090}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

URL="http://localhost:${PORT}/v3/"
echo "──────────────────────────────────────────────────────────────"
echo "  Biocity Healthcare — v3 (local mirror)"
echo "  Serving:  $DIR"
echo "  Open:     $URL"
echo "  Stop:     Ctrl-C"
echo "──────────────────────────────────────────────────────────────"

# Open the browser (macOS) a moment after the server starts.
( sleep 1; command -v open >/dev/null 2>&1 && open "$URL" ) &

exec python3 -m http.server "$PORT" --bind 127.0.0.1
