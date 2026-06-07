FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY deployment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .
COPY --from=frontend-build /app/frontend/build /app/frontend/build

EXPOSE 10000

CMD ["sh", "-c", "exec gunicorn deployment.app:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --worker-class gthread --threads 16 --timeout 120 --access-logfile - --error-logfile -"]
