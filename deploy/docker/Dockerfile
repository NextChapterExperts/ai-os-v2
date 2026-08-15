# ==============================================================================
# AI-OS v2 Core Platform Appliance — Unified Multi-Stage Production Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Next.js Console Web Build
# ------------------------------------------------------------------------------
FROM node:22-alpine AS web-builder
WORKDIR /app/console-web

COPY core/console-web/package*.json ./
RUN npm install --legacy-peer-deps

COPY core/console-web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Unified Production Runner (FastAPI + Node Runtime + SQLite)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# System-Abhängigkeiten installieren (Node.js 22 LTS, Curl, SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    sqlite3 \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python Abhängigkeiten installieren
COPY pyproject.toml ./
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pyyaml \
    httpx \
    sentence-transformers \
    fastembed

# Python Orchestrator Source kopieren
COPY core/ /app/core/
COPY scripts/ /app/scripts/

# Vorkompiliertes Web-Frontend aus Stage 1 übernehmen
COPY --from=web-builder /app/console-web /app/core/console-web

# Persistenter Daten-Layer
ENV DATA_DIR=/app/data
ENV ORCHESTRATOR_URL=http://127.0.0.1:8091
ENV PORT=8090
ENV HOST=0.0.0.0

RUN mkdir -p /app/data

# Entrypoint Skript
RUN cat << "EOF" > /app/entrypoint.sh
#!/bin/bash
set -e

echo "🚀 Starte AI-OS v2 Core Platform Appliance..."
echo "📁 Persistentes Datenverzeichnis: ${DATA_DIR}"

# 1. FastAPI Orchestrator im Hintergrund starten (Port 8091)
python3 -m uvicorn core.orchestrator.server:app --host 0.0.0.0 --port 8091 &

# 2. Next.js Console Web starten (Port 8090)
cd /app/core/console-web
npx next start -p 8090 -H 0.0.0.0
EOF

RUN chmod +x /app/entrypoint.sh

EXPOSE 8090 8091

VOLUME ["/app/data"]

CMD ["/app/entrypoint.sh"]
