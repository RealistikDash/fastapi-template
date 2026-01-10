#!/bin/bash
set -euo pipefail

if [ -z "$APP_COMPONENT" ]; then
  echo "Bootstrap - Please set APP_COMPONENT"
  exit 1
fi

if [ $APP_COMPONENT = "fastapi" ]; then
  exec ./scripts/run_fastapi.sh
else
  echo "Bootstrap - Unknown APP_COMPONENT: $APP_COMPONENT"
  exit 1
fi