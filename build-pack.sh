#!/usr/bin/env bash
# Build a deployment "pack" (like a WAR for Tomcat): one tarball to copy to the server.
# Requires .NET 8 to be installed on the server. Smaller than self-contained.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
OUT_DIR="bin/Release/net8.0/linux-x64/publish"
PACK_NAME="LschannelFun-pack.tar.gz"

echo "Building pack (framework-dependent, linux-x64)..."
dotnet publish -c Release -p:PublishProfile=Properties/PublishProfiles/pack.pubxml

echo "Creating pack: $PACK_NAME"
tar -czf "$PACK_NAME" -C "$OUT_DIR" .

echo "Done. Copy to server and run:"
echo "  scp $PACK_NAME user@server:/opt/"
echo "  ssh user@server"
echo "  cd /opt && mkdir -p lschannelfun && tar -xzf $PACK_NAME -C lschannelfun && cd lschannelfun"
echo "  ASPNETCORE_URLS=http://0.0.0.0:80 ./LschannelFun"
