.PHONY: install up down pipeline test lint

install:   ## local dev environment
	pip install -e ".[dev]"

up:        ## start Weaviate + app
	docker-compose up -d --build

down:
	docker-compose down

pipeline:  ## first run: clean data, create schema, embed + ingest (uses OpenAI credits)
	docker-compose run --rm app python scripts/process_data.py
	docker-compose run --rm app python scripts/create_schema.py
	docker-compose run --rm app python scripts/ingest_data.py

test:
	pytest -q

lint:
	ruff check . --select E9,F,B
