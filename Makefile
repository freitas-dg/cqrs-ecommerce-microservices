.PHONY: help up down build logs test test-user test-order migrate seed clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:
	@if not exist .env copy .env.example .env
	@$(MAKE) build
	@$(MAKE) up
	@echo "Waiting for services to be healthy..."
	@timeout /t 15
	@$(MAKE) migrate
	@echo "Setup complete! APIs available at:"
	@echo "  User API:  http://localhost:8000/docs"
	@echo "  Order API: http://localhost:8001/api/docs"
	@echo "  RabbitMQ:  http://localhost:15672"
	@echo "  Grafana:   http://localhost:3000"

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@timeout /t 15
	@$(MAKE) migrate

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

logs-user:
	docker-compose logs -f user-api

logs-order:
	docker-compose logs -f order-api

logs-otel:
	docker-compose logs -f otel-collector loki tempo grafana promtail

restart:
	docker-compose restart user-api order-api
migrate:
	docker-compose exec user-api alembic upgrade head

migrate-user:
	docker-compose exec user-api alembic upgrade head

migrate-order:
	docker-compose exec order-api flask db upgrade

test: test-user test-order

test-user:
	docker-compose exec user-api pytest -v --tb=short

test-order:
	docker-compose exec order-api pytest -v --tb=short

test-cov:
	docker-compose exec user-api pytest -v --cov=app --cov-report=term-missing
	docker-compose exec order-api pytest -v --cov=app --cov-report=term-missing

shell-user:
	docker-compose exec user-api /bin/sh

shell-order:
	docker-compose exec order-api /bin/sh

clean:
	docker-compose down -v --rmi local
	@echo "All containers, volumes and images removed."
