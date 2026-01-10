#!/bin/bash
set -euo pipefail

# URL-encode a string (pure bash, no external dependencies)
urlencode() {
    local LC_ALL=C string="$1" i c
    for ((i = 0; i < ${#string}; i++)); do
        c="${string:i:1}"
        case "$c" in
            [a-zA-Z0-9.~_-]) printf '%s' "$c" ;;
            *) printf '%%%02X' "'$c" ;;
        esac
    done
}

ENCODED_PASSWORD=$(urlencode "${MYSQL_PASSWORD}")
MYSQL_DSN="mysql://${MYSQL_USER}:${ENCODED_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_TCP_PORT})/${MYSQL_DATABASE}"

echo "Performing migrations if required."
go-migrate -path /migrations -database "${MYSQL_DSN}" up
