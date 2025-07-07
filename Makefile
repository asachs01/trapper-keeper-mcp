.PHONY: help install install-dev clean test test-fast test-cov lint format type-check build upload upload-test docs docs-serve docker-build docker-run docker-push pre-commit setup-hooks bump-patch bump-minor bump-major

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := trapper-keeper-mcp
DOCKER_IMAGE := $(PROJECT_NAME)
DOCKER_TAG := latest
DOCKER_REGISTRY := ghcr.io/yourusername
SRC_DIR := src
TEST_DIR := tests

# Color codes for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)$(PROJECT_NAME) Development Commands$(NC)"
	@echo "$(CYAN)======================================$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install the package in production mode
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .

install-dev: ## Install the package with all development dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev,test,docs]"
	$(MAKE) setup-hooks

setup-hooks: ## Setup git pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit install --hook-type pre-push

clean: ## Clean build artifacts and cache files
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .coverage.*
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .tox/
	@echo "$(GREEN)✓ Clean complete$(NC)"

test: ## Run all tests with coverage
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-fast: ## Run tests in parallel without coverage
	@echo "$(CYAN)Running tests in parallel...$(NC)"
	$(PYTHON) -m pytest -n auto --maxfail=3

test-cov: ## Run tests and open coverage report
	@echo "$(CYAN)Running tests with coverage report...$(NC)"
	$(PYTHON) -m pytest --cov=$(SRC_DIR) --cov-report=html
	@echo "$(GREEN)Opening coverage report...$(NC)"
	open htmlcov/index.html || xdg-open htmlcov/index.html

lint: ## Run all linting checks
	@echo "$(CYAN)Running linting checks...$(NC)"
	@echo "$(YELLOW)Running ruff...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running black check...$(NC)"
	black --check $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running isort check...$(NC)"
	isort --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ All linting checks passed$(NC)"

format: ## Format code with black and isort
	@echo "$(CYAN)Formatting code...$(NC)"
	@echo "$(YELLOW)Running isort...$(NC)"
	isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running black...$(NC)"
	black $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running ruff fix...$(NC)"
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

type-check: ## Run mypy type checking
	@echo "$(CYAN)Running type checking...$(NC)"
	mypy $(SRC_DIR)

build: clean ## Build distribution packages
	@echo "$(CYAN)Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Build complete$(NC)"
	@ls -la dist/

upload-test: build ## Upload to TestPyPI
	@echo "$(CYAN)Uploading to TestPyPI...$(NC)"
	$(PYTHON) -m twine upload --repository testpypi dist/*

upload: build ## Upload to PyPI
	@echo "$(RED)WARNING: Uploading to PyPI!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel...$(NC)"
	@sleep 3
	$(PYTHON) -m twine upload dist/*

docs: ## Build documentation
	@echo "$(CYAN)Building documentation...$(NC)"
	mkdocs build
	@echo "$(GREEN)✓ Documentation built$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(CYAN)Serving documentation at http://localhost:8000$(NC)"
	mkdocs serve

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):latest
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run Docker container
	@echo "$(CYAN)Running Docker container...$(NC)"
	docker run -it --rm \
		-v $(PWD)/data:/app/data \
		-p 3000:3000 \
		--env-file .env \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push: ## Push Docker image to registry
	@echo "$(CYAN)Pushing Docker image to registry...$(NC)"
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):latest
	docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):latest
	@echo "$(GREEN)✓ Docker image pushed$(NC)"

pre-commit: ## Run pre-commit on all files
	@echo "$(CYAN)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

bump-patch: ## Bump patch version (x.y.Z)
	@echo "$(CYAN)Bumping patch version...$(NC)"
	git tag -a v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1"."$$2"."$$3+1}') -m "Release v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1"."$$2"."$$3+1}')"
	@echo "$(GREEN)✓ Version bumped. Don't forget to push tags!$(NC)"

bump-minor: ## Bump minor version (x.Y.z)
	@echo "$(CYAN)Bumping minor version...$(NC)"
	git tag -a v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1"."$$2+1".0"}') -m "Release v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1"."$$2+1".0"}')"
	@echo "$(GREEN)✓ Version bumped. Don't forget to push tags!$(NC)"

bump-major: ## Bump major version (X.y.z)
	@echo "$(CYAN)Bumping major version...$(NC)"
	git tag -a v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1+1".0.0"}') -m "Release v$$(git describe --tags --abbrev=0 | sed 's/v//' | awk -F. '{print $$1+1".0.0"}')"
	@echo "$(GREEN)✓ Version bumped. Don't forget to push tags!$(NC)"

# Development workflow shortcuts
dev: install-dev ## Setup development environment
	@echo "$(GREEN)✓ Development environment ready$(NC)"

check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed$(NC)"

ci: check ## Run CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

release: check build ## Prepare for release (run checks and build)
	@echo "$(GREEN)✓ Ready for release$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Review dist/ contents"
	@echo "  2. Run 'make upload-test' to test on TestPyPI"
	@echo "  3. Run 'make upload' to publish to PyPI"