FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Expect build context = repo root when using deploy/core.yml — for local image:
# docker build -f core/orchestrator/Dockerfile -t aios-orchestrator .
COPY core/orchestrator /app/core/orchestrator
COPY customers /app/customers
ENV PYTHONPATH=/app
EXPOSE 8091
CMD ["uvicorn", "core.orchestrator.server:app", "--host", "0.0.0.0", "--port", "8091"]
