#!/bin/bash
set -euo pipefail

echo "Starting API..."
exec uvicorn comparison_service.main:asgi_app \
    --host "${COMPARISON_SERVICE_HTTP_HOST:=0.0.0.0}" \
    --port "${COMPARISON_SERVICE_HTTP_PORT:=80}" \
    --reload # TODO: Handle reloads properly in production
