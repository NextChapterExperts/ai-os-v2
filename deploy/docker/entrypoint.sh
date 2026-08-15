#!/bin/bash

echo "🚀 Starting AI-OS Core Platform Appliance..."

mkdir -p /app/data/logs /app/data/db /app/data/uploads

echo "Starting Orchestrator Engine (FastAPI on port 8091)..."
python3 -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port 8091 &
PID_ORCH=$!

echo "Waiting for Orchestrator to become healthy..."
sleep 2

echo "Starting Web Console (Next.js Standalone on port 8090)..."
export PORT=8090
export HOSTNAME=0.0.0.0

if [ -f "/app/core/console-web/.next/standalone/server.js" ]; then
  node /app/core/console-web/.next/standalone/server.js &
elif [ -f "/app/core/console-web/server.js" ]; then
  node /app/core/console-web/server.js &
else
  cd /app/core/console-web && npx next start -p 8090 -H 0.0.0.0 &
fi
PID_WEB=$!

# Trap signals for graceful shutdown
trap "kill -TERM $PID_ORCH $PID_WEB 2>/dev/null; exit 0" SIGINT SIGTERM

echo "✓ AI-OS Core Platform Appliance running [PIDs: Orchestrator=$PID_ORCH, Web=$PID_WEB]"

# Keep running as long as both processes are alive
while kill -0 $PID_ORCH 2>/dev/null && kill -0 $PID_WEB 2>/dev/null; do
  sleep 2
done

echo "⚠️ One of the services exited. Terminating container."
kill -TERM $PID_ORCH $PID_WEB 2>/dev/null || true
exit 1
