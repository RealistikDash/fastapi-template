#!/usr/bin/make
build:
	docker compose build

run:
	docker compose up app

run-d:
	docker compose up -d app

lint:
	pre-commit run --all-files

test:
	python3 -m pytest tests/ -v

test-cov:
	python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# Development tools
phpmyadmin:
	docker compose --profile dev up phpmyadmin
