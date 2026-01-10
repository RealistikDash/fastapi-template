#!/usr/bin/make
build:
	docker compose build

run:
	docker compose up app

run-d:
	docker compose up -d app

lint:
	pre-commit run --all-files

# Development tools
phpmyadmin:
	docker compose --profile dev up phpmyadmin
