SHELL := /bin/sh
PYTHON := python3

.PHONY: run
run: swagger
	@echo "Starting server..."
	go run ./cmd/server

.PHONY: swagger
swagger:
	@echo "Generating Swagger documentation..."
	swag init -g cmd/server/main.go -o docs

.PHONY: build
build: swagger
	@echo "Building server binary..."
	go build -o bin/server.exe ./cmd/server

.PHONY: clone
clone: clone-repos clone-docs

.PHONY: clone-repos
clone-repos:
	@echo "Cloning Motoko code repositories..."
	$(PYTHON) scripts/clone_repos.py

.PHONY: clone-docs
clone-docs:
	@echo "Cloning Motoko documentation..."
	$(PYTHON) scripts/clone_docs.py

.PHONY: ingest
ingest: ingest-samples ingest-docs

.PHONY: ingest-samples
ingest-samples:
	@echo "Ingesting Motoko code samples..."
	$(PYTHON) scripts/ingest_samples.py

.PHONY: ingest-docs
ingest-docs:
	@echo "Ingesting Motoko documentation..."
	$(PYTHON) scripts/ingest_docs.py

.PHONY: setup
setup: clone ingest
	@echo "Setup complete! ChromaDB is ready."

.PHONY: clean-data
clean-data:
	@echo "Removing all cloned data..."
	rm -rf data/motoko_code_samples
	rm -rf data/motoko_official_docs
	rm -rf data/chromadb
	rm -f data/motoko_coder.db
	rm -f data/*.db-*
	@echo "Data cleaned."

# Docker commands
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	docker-compose build

.PHONY: up
up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Backend is running at http://localhost:8080"

.PHONY: docker-down
docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

.PHONY: docker-logs
docker-logs:
	@echo "Viewing Docker logs (Ctrl+C to exit)..."
	docker-compose logs -f

.PHONY: docker-restart
docker-restart:
	@echo "Restarting Docker containers..."
	docker-compose restart

.PHONY: docker-rebuild
docker-rebuild:
	@echo "Rebuilding and restarting Docker containers..."
	docker-compose up -d --build

.PHONY: docker-clean
docker-clean:
	@echo "Stopping and removing Docker containers and volumes..."
	docker-compose down -v
	@echo "Docker cleanup complete."

.PHONY: docker-ps
docker-ps:
	@echo "Docker container status:"
	docker-compose ps

.PHONY: docker-shell
docker-shell:
	@echo "Opening shell in backend container..."
	docker-compose exec icp-coder /bin/sh

# Development environment with live reload
.PHONY: dev-up
dev-up:
	@echo "Starting development environment with live reload..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development backend is running at http://localhost:8080"
	@echo "Code changes will trigger automatic rebuild"

.PHONY: dev-down
dev-down:
	@echo "Stopping development containers..."
	docker-compose -f docker-compose.dev.yml down

.PHONY: dev-logs
dev-logs:
	@echo "Viewing development logs (Ctrl+C to exit)..."
	docker-compose -f docker-compose.dev.yml logs -f

.PHONY: dev-rebuild
dev-rebuild:
	@echo "Rebuilding development environment..."
	docker-compose -f docker-compose.dev.yml up -d --build

.PHONY: dev-restart
dev-restart:
	@echo "Restarting development containers..."
	docker-compose -f docker-compose.dev.yml restart

.PHONY: dev-shell
dev-shell:
	@echo "Opening shell in development container..."
	docker-compose -f docker-compose.dev.yml exec backend /bin/bash

.PHONY: dev-clean
dev-clean:
	@echo "Stopping and removing development containers and volumes..."
	docker-compose -f docker-compose.dev.yml down -v
	@echo "Development cleanup complete."

.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make run              - Run the backend server (auto-generates Swagger docs)"
	@echo "  make build            - Build the backend binary (auto-generates Swagger docs)"
	@echo "  make swagger          - Generate Swagger documentation only"
	@echo ""
	@echo "Data Management:"
	@echo "  make clone            - Clone all repositories and documentation"
	@echo "  make clone-repos      - Clone Motoko code repositories only"
	@echo "  make clone-docs       - Clone Motoko documentation only"
	@echo "  make ingest           - Ingest all data into ChromaDB"
	@echo "  make ingest-samples   - Ingest code samples only"
	@echo "  make ingest-docs      - Ingest documentation only"
	@echo "  make setup            - Complete setup (clone + ingest)"
	@echo "  make clean-data       - Remove all cloned data and ChromaDB"
	@echo ""
	@echo "Docker (Production):"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make up               - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs (follow mode)"
	@echo "  make docker-restart   - Restart Docker containers"
	@echo "  make docker-rebuild   - Rebuild and restart containers"
	@echo "  make docker-clean     - Remove containers and volumes"
	@echo "  make docker-ps        - Show container status"
	@echo "  make docker-shell     - Open shell in backend container"
	@echo ""
	@echo "Docker (Development with Live Reload):"
	@echo "  make dev-up           - Start dev environment (auto-reload on code changes)"
	@echo "  make dev-down         - Stop dev containers"
	@echo "  make dev-logs         - View dev logs (follow mode)"
	@echo "  make dev-restart      - Restart dev containers"
	@echo "  make dev-rebuild      - Rebuild dev containers"
	@echo "  make dev-shell        - Open bash shell in dev container"
	@echo "  make dev-clean        - Remove dev containers and volumes"
	@echo ""
	@echo "Other:"
	@echo "  make help             - Show this help message"
