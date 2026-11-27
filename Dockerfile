# Optional API image for local/demo healthchecks. Dev workflow still uses uvicorn on the host.
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

ENV API_HOST=0.0.0.0
ENV API_PORT=8003
EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8003/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
