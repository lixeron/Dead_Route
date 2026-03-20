.PHONY: run test lint docker docker-run clean help

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run the game locally
	cd dead_route && python3 main.py

test: ## Run the test suite
	cd dead_route && python3 -m pytest tests/ -v --tb=short

test-quick: ## Run tests without verbose output
	cd dead_route && python3 -m pytest tests/ -q

test-cov: ## Run tests with coverage report
	cd dead_route && python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

lint: ## Run linting checks
	python3 -m py_compile dead_route/main.py
	@echo "Checking all Python files compile..."
	@find dead_route -name "*.py" ! -name "__init__.py" -exec python3 -m py_compile {} \;
	@echo "All files compile successfully."

docker: ## Build Docker image
	docker build -t dead-route:latest .

docker-run: docker ## Build and run in Docker
	docker run -it --rm dead-route:latest

compose-up: ## Run with docker-compose
	docker compose run --rm game

clean: ## Remove build artifacts and databases
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.db" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

version: ## Show project stats
	@echo "Dead Route — Project Statistics"
	@echo "================================"
	@echo -n "Python modules: " && find dead_route -name "*.py" ! -name "__init__.py" | wc -l
	@echo -n "JSON data files: " && find dead_route -name "*.json" | wc -l
	@echo -n "Total lines of code: " && find dead_route \( -name "*.py" -o -name "*.json" \) ! -name "__init__.py" -exec cat {} + | wc -l
	@echo -n "Test files: " && find dead_route/tests -name "test_*.py" | wc -l
