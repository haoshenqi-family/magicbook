#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

PID=$(ss -tlnp 2>/dev/null | grep ':8085 ' | grep -oP 'pid=\K[0-9]+')
if [ -n "$PID" ]; then
    echo "Stopping Calibre-Web (PID $PID)..."
    kill "$PID"
    sleep 3
fi

echo "Starting Calibre-Web..."
nohup python3 cps.py > /tmp/calibre-web.log 2>&1 &
for i in $(seq 1 20); do
    sleep 2
    NEW_PID=$(ss -tlnp 2>/dev/null | grep ':8085 ' | grep -oP 'pid=\K[0-9]+')
    [ -n "$NEW_PID" ] && break
done
if [ -n "$NEW_PID" ]; then
    echo "Calibre-Web started on port 8085 (PID $NEW_PID)"
else
    echo "Failed to start after 40s. Check /tmp/calibre-web.log"
    tail -20 /tmp/calibre-web.log
fi