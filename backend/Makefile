SHELL := /bin/sh
PYTHON := python3
PIP := pip3
VENV_DIR := venv

# Python dependency management
.PHONY: venv
venv:
	@echo "Creating Python virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created. Activate with: source $(VENV_DIR)/bin/activate"

.PHONY: deps
deps:
	@echo "Installing Python dependencies..."
	$(PIP) install -r requirements.txt

.PHONY: deps-upgrade
deps-upgrade:
	@echo "Upgrading Python dependencies..."
	$(PIP) install --upgrade -r requirements.txt

.PHONY: install
install: deps
	@echo "Installing Go dependencies..."
	go mod download
	@echo "All dependencies installed!"

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

# Docker commands (Production)
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	docker compose build

.PHONY: docker-up
docker-up:
	@echo "Starting Docker containers..."
	docker compose up -d
	@echo "Backend is running at http://localhost:8080"

.PHONY: up
up:
	$(MAKE) docker-build
	$(MAKE) docker-up

.PHONY: docker-down
docker-down:
	@echo "Stopping Docker containers..."
	docker compose down

.PHONY: docker-logs
docker-logs:
	@echo "Viewing Docker logs (Ctrl+C to exit)..."
	docker compose logs -f

.PHONY: docker-restart
docker-restart:
	@echo "Restarting Docker containers..."
	docker compose restart

.PHONY: docker-rebuild
docker-rebuild:
	@echo "Rebuilding and restarting Docker containers..."
	docker compose up -d --build

.PHONY: docker-clean
docker-clean:
	@echo "Stopping and removing Docker containers and volumes..."
	docker compose down -v
	@echo "Docker cleanup complete."

# Docker commands (Development)
.PHONY: dev-build
dev-build:
	@echo "Building development Docker image..."
	docker compose -f docker-compose.dev.yml build

.PHONY: dev-up
dev-up:
	@echo "Starting development containers with live reload..."
	docker compose -f docker-compose.dev.yml up -d
	@echo "Development backend is running at http://localhost:8080"
	@echo "Live reload enabled - code changes will trigger automatic rebuilds"

.PHONY: dev
dev:
	$(MAKE) dev-build
	$(MAKE) dev-up

.PHONY: dev-down
dev-down:
	@echo "Stopping development containers..."
	docker compose -f docker-compose.dev.yml down

.PHONY: dev-logs
dev-logs:
	@echo "Viewing development logs (Ctrl+C to exit)..."
	docker compose -f docker-compose.dev.yml logs -f

.PHONY: dev-restart
dev-restart:
	@echo "Restarting development containers..."
	docker compose -f docker-compose.dev.yml restart

.PHONY: dev-rebuild
dev-rebuild:
	@echo "Rebuilding and restarting development containers..."
	docker compose -f docker-compose.dev.yml up -d --build

.PHONY: dev-clean
dev-clean:
	@echo "Stopping and removing development containers and volumes..."
	docker compose -f docker-compose.dev.yml down -v
	@echo "Development cleanup complete."

.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install          - Install all dependencies (Python + Go)"
	@echo "  make deps             - Install Python dependencies from requirements.txt"
	@echo "  make deps-upgrade     - Upgrade Python dependencies"
	@echo "  make venv             - Create Python virtual environment"
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
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make up               - Build and start Docker containers (docker-build + docker-up)"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs (follow mode)"
	@echo "  make docker-restart   - Restart Docker containers"
	@echo "  make docker-rebuild   - Rebuild and restart containers"
	@echo "  make docker-clean     - Remove containers and volumes"
	@echo ""
	@echo "Docker (Development):"
	@echo "  make dev-build        - Build development Docker image"
	@echo "  make dev-up           - Start development containers with live reload"
	@echo "  make dev              - Build and start dev containers (dev-build + dev-up)"
	@echo "  make dev-down         - Stop development containers"
	@echo "  make dev-logs         - View development logs (follow mode)"
	@echo "  make dev-restart      - Restart development containers"
	@echo "  make dev-rebuild      - Rebuild and restart dev containers"
	@echo "  make dev-clean        - Remove dev containers and volumes"
