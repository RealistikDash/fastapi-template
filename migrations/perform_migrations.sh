#!/bin/bash
set -euo pipefail

MYSQL_DSN="mysql://${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_TCP_PORT})/${MYSQL_DATABASE}"

echo "Performing migrations if required."
go-migrate -path /migrations -database $MYSQL_DSN up
