#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../infra/docker/docker-compose.yml"

echo "=== RAG Knowledge Base - Local Setup ==="
echo ""

echo "[1/3] Starting services..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo ""
echo "[2/3] Waiting for backend to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
BACKEND_READY=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ] && [ $BACKEND_READY -eq 0 ]; do
    if curl -s -f "http://localhost:8000/api/v1/health" > /dev/null 2>&1; then
        BACKEND_READY=1
        echo "Backend is ready!"
    else
        ATTEMPT=$((ATTEMPT + 1))
        echo "  Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
        sleep 2
    fi
done

if [ $BACKEND_READY -eq 0 ]; then
    echo "WARNING: Backend may not be fully ready yet. Check logs with: docker compose -f $COMPOSE_FILE logs -f backend"
fi

echo ""
echo "[3/3] Setup complete!"
echo ""
echo "=== Service URLs ==="
echo "  API Docs:   http://localhost:8000/docs"
echo "  API Base:   http://localhost:8000/api/v1"
echo "  Frontend:   http://localhost:3000"
echo "  MinIO:      http://localhost:9001 (user: minio, pass: minio12345)"
echo ""
echo "=== Default Admin ==="
echo "  Email:      admin@example.com"
echo "  Password:   Admin123!"
echo ""
echo "=== Useful Commands ==="
echo "  View logs:  docker compose -f $COMPOSE_FILE logs -f"
echo "  Stop:       docker compose -f $COMPOSE_FILE down"
echo "  Restart:    docker compose -f $COMPOSE_FILE restart"
echo ""
