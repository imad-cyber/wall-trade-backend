"""
Makefile commands for common development tasks.
Run with: make <command>
"""

.PHONY: help install dev test lint format clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make dev              - Run development server"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters (flake8, mypy)"
	@echo "  make format           - Format code with black and isort"
	@echo "  make clean            - Clean up cache and build files"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run Docker container"

install:
	pip install -r requirements.txt

dev:
	python run.py

test:
	pytest

lint:
	flake8 app
	mypy app

format:
	black app
	isort app

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

docker-build:
	docker build -t wall-trade-backend:latest .

docker-run:
	docker-compose up -d

docker-logs:
	docker-compose logs -f app

docker-stop:
	docker-compose down
