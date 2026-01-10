#!/bin/bash
set -euo pipefail

echo "Starting API..."

UVICORN_ARGS=(
    "--host" "${APP_HTTP_HOST:=0.0.0.0}"
    "--port" "${APP_HTTP_PORT:=80}"
)

if [ "${APP_DEV_MODE:-false}" = "true" ]; then
    echo "Development mode enabled."
    UVICORN_ARGS+=("--reload")
fi

exec uvicorn app.main:asgi_app "${UVICORN_ARGS[@]}"
