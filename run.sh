#!/usr/bin/env bash
# SANJEEVNI SYSTEM LAUNCHER  (works from any folder - no hard-coded paths)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
pkill -f "python3.*server.py" 2>/dev/null
sleep 0.3
echo "Starting Sanjeevni gateway... (Ctrl+C to stop)"
echo "  Laptop:  http://localhost:8080/"
echo "  Phone :  open the https://<IP>:8443/rover link printed below (Advanced -> Proceed)"
exec python3 server.py
