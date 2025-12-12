.PHONY: install lint format test check run-local

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt -r requirements-dev.txt

lint:
	ruff check .
	black --check .
	isort --check-only .

format:
	ruff check --fix .
	black .
	isort .

test:
	pytest -q

check: lint test

run-local:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
