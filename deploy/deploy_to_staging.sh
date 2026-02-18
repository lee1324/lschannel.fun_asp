#!/bin/bash
# Build and deploy to staging folder (port 8081).
# Run from repo root (e.g. on your machine or CI). Or on server: clone/pull then run this.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Default: staging folder next to repo (works on Mac/Linux). On server set STAGING_DIR=/home/ls/lschannel.fun_staging
STAGING_DIR="${STAGING_DIR:-$REPO_ROOT/deploy/staging}"

echo "=== Deploy to staging ==="
echo "Repo: $REPO_ROOT"
echo "Staging dir: $STAGING_DIR"

cd "$REPO_ROOT"
dotnet publish -c Release -o "$STAGING_DIR"

mkdir -p "$STAGING_DIR/logs"
echo "Published to $STAGING_DIR"

# Optional: start/restart staging app on port 8081 (if run on server)
if command -v lsof &>/dev/null && lsof -i :8081 -sTCP:LISTEN -t &>/dev/null; then
    echo "Stopping existing staging app (8081)..."
    kill $(lsof -i :8081 -sTCP:LISTEN -t) 2>/dev/null || true
    sleep 2
fi
cd "$STAGING_DIR"
export ASPNETCORE_URLS="http://0.0.0.0:8081"
nohup dotnet LschannelFun.dll >> logs/staging_stdout.log 2>> logs/staging_stderr.log &
echo "Staging app started on port 8081 (PID $!)."
echo "=== Done. Test at https://staging.lschannel.fun (or your staging URL). ==="
