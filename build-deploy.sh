#!/usr/bin/env bash
# Build a self-contained deployment package for CentOS 8 (Linux x64).
# Like building a WAR for Tomcat: one tarball to copy to the server and run.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
OUT_DIR="bin/Release/net8.0/linux-x64/publish"
TARBALL="LschannelFun-linux-x64.tar.gz"

echo "Publishing for linux-x64 (self-contained)..."
dotnet publish -c Release -p:PublishProfile=Properties/PublishProfiles/linux-x64.pubxml

echo "Creating deployment tarball: $TARBALL"
tar -czf "$TARBALL" -C "$OUT_DIR" .

echo "Done. Copy to CentOS 8 and run:"
echo "  scp $TARBALL user@server:/opt/"
echo "  ssh user@server"
echo "  cd /opt && tar -xzf $TARBALL && ASPNETCORE_URLS=http://0.0.0.0:8080 ./LschannelFun"
echo ""
echo "Note: Port 8080 is used so nginx can bind to port 80 for HTTPS reverse proxy."
