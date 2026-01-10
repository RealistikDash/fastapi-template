#!/bin/bash
set -euo pipefail

echo "Starting API..."
exec uvicorn app.main:asgi_app \
    --host "${APP_HTTP_HOST:=0.0.0.0}" \
    --port "${APP_HTTP_PORT:=80}" \
    --reload # TODO: Handle reloads properly in production
