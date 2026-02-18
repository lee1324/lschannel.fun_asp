#!/bin/bash
# Promote staging to release: copy staging app folder to release, restart release app.
# Run on the server. Uses ports 8081 (staging) and 8080 (release).

set -e

# Defaults: repo-relative paths (work on Mac/local). On server set STAGING_DIR and RELEASE_DIR.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGING_DIR="${STAGING_DIR:-$REPO_ROOT/deploy/staging}"
RELEASE_DIR="${RELEASE_DIR:-$REPO_ROOT/deploy/release}"
APP_NAME="LschannelFun"

echo "=== Promote staging to release ==="
echo "Staging: $STAGING_DIR"
echo "Release: $RELEASE_DIR"

if [ ! -d "$STAGING_DIR" ]; then
    echo "Error: Staging directory not found: $STAGING_DIR"
    exit 1
fi

# Stop release app (port 8080)
if command -v lsof &>/dev/null; then
    if lsof -i :8080 -sTCP:LISTEN -t &>/dev/null; then
        echo "Stopping release app (port 8080)..."
        kill $(lsof -i :8080 -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 3
    fi
else
    pkill -f "$APP_NAME" 2>/dev/null || true
    sleep 2
fi

# Sync staging → release (keeps release dir, replaces contents)
mkdir -p "$RELEASE_DIR"
echo "Syncing staging to release..."
if command -v rsync &>/dev/null; then
    rsync -a --delete "$STAGING_DIR/" "$RELEASE_DIR/"
else
    rm -rf "$RELEASE_DIR"/*
    cp -a "$STAGING_DIR"/* "$RELEASE_DIR"/
fi

# Start release app (port 8080)
cd "$RELEASE_DIR"
mkdir -p logs
echo "Starting release app on port 8080..."
export ASPNETCORE_URLS="http://0.0.0.0:8080"
if [ -f LschannelFun.dll ]; then
    nohup dotnet LschannelFun.dll >> logs/release_stdout.log 2>> logs/release_stderr.log &
else
    nohup dotnet run >> logs/release_stdout.log 2>> logs/release_stderr.log &
fi
echo "Release app started (PID $!)."
echo "=== Done. Main site (port 8080) now serves the promoted build. ==="
