#!/bin/bash
set -e

echo "🚀 Starting AI-OS Core Platform Appliance..."

mkdir -p /app/data/logs /app/data/db /app/data/uploads

echo "Starting Orchestrator Engine (FastAPI on port 8091)..."
python3 -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port 8091 &

echo "Waiting for Orchestrator to become healthy..."
sleep 2

echo "Starting Web Console (Next.js Standalone on port 8090)..."
export PORT=8090
export HOSTNAME=0.0.0.0

if [ -f "/app/core/console-web/.next/standalone/server.js" ]; then
  cd /app/core/console-web/.next/standalone
  node server.js &
elif [ -f "/app/core/console-web/.next/standalone/app/core/console-web/server.js" ]; then
  cd /app/core/console-web/.next/standalone/app/core/console-web
  node server.js &
elif [ -f "/app/core/console-web/server.js" ]; then
  cd /app/core/console-web
  node server.js &
else
  cd /app/core/console-web
  npx --yes next start -p 8090 -H 0.0.0.0 &
fi

# Keep container alive
wait -n
