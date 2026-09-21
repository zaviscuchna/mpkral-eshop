#!/bin/bash
# Nahled e-shopu M+P Kral. Okno nechej otevrene, drzi server.
cd "$(dirname "$0")" || exit 1
PORT=8778
if ! curl -s -o /dev/null "http://localhost:$PORT/index.html"; then
  python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
  sleep 1
fi
open "http://localhost:$PORT/index.html"
echo "Nahled bezi na http://localhost:$PORT/"
echo "Az skoncis, zavri tohle okno."
wait
