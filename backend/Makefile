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

.PHONY: docker-up
docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Backend is running at http://localhost:8080"

.PHONY: up
up:
	$(MAKE) docker-build
	$(MAKE) docker-up

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
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs (follow mode)"
	@echo "  make docker-restart   - Restart Docker containers"
	@echo "  make docker-rebuild   - Rebuild and restart containers"
	@echo "  make docker-clean     - Remove containers and volumes"
	@echo "  make docker-ps        - Show container status"
	@echo "  make docker-shell     - Open shell in backend container"
