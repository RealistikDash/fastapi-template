FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements/main.txt .
RUN pip install -r main.txt --no-cache-dir

# Application pre-requisites
COPY ./scripts /app/scripts
COPY ./logging.yaml /app/logging.yaml


# Copy the application
COPY ./app /app/app
WORKDIR /app

ENTRYPOINT ["/app/scripts/bootstrap.sh"]