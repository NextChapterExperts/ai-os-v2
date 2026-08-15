#!/bin/bash
set -e

echo "🚀 Starting AI-OS Core Platform Appliance..."

mkdir -p /app/data/logs /app/data/db /app/data/uploads

echo "Starting Orchestrator Engine (FastAPI on port 8091)..."
python3 -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port 8091 &

echo "Waiting for Orchestrator to become healthy..."
sleep 2

echo "Starting Web Console (Next.js on port 8090)..."
cd /app/core/console-web
export PORT=8090
export HOSTNAME=0.0.0.0
node node_modules/.bin/next start -p 8090 -H 0.0.0.0 &

# Keep container alive
wait -n
