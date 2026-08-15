# ==============================================================================
# AI-OS v2 Core Platform Appliance — Unified Multi-Stage Production Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Next.js Console Web Build
# ------------------------------------------------------------------------------
FROM node:22-alpine AS web-builder
WORKDIR /app/console-web

COPY core/console-web/package*.json ./
RUN npm install --legacy-peer-deps --ignore-scripts

COPY core/console-web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Unified Production Runner (FastAPI + Node Runtime + SQLite)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# Node.js 22 LTS Runtime direkt aus offiziellem Image übernehmen
COPY --from=node:22-bookworm-slim /usr/local/ /usr/local/

# System-Abhängigkeiten installieren (Curl, Git, SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python Abhängigkeiten installieren
COPY core/orchestrator/requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Plattform Module kopieren
COPY core/ /app/core/
COPY sdk/ /app/sdk/
COPY config/ /app/config/
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
COPY deploy/docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8090 8091

VOLUME ["/app/data"]

CMD ["/app/entrypoint.sh"]
