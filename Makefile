.PHONY: help install sync test lint format run-api run-frontend ingest-data evaluate clean

help:
	@echo "University QA - Makefile commands (powered by uv)"
	@echo "--------------------------------------------------"
	@echo "  make install       : Create venv and install dependencies using uv"
	@echo "  make sync          : Sync project dependencies with uv.lock"
	@echo "  make test          : Run tests with pytest"
	@echo "  make lint          : Check code quality with ruff"
	@echo "  make format        : Auto-format code with ruff"
	@echo "  make run-api       : Run FastAPI development server"
	@echo "  make run-frontend  : Run Streamlit UI"
	@echo "  make ingest-data   : Process raw documents to corpus"
	@echo "  make evaluate      : Run evaluation benchmark"
	@echo "  make clean         : Clean cache and temporary files"

install:
	uv venv
	uv sync

sync:
	uv sync

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format .

run-api:
	uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	uv run streamlit run frontend/app.py

ingest-data:
	uv run python scripts/ingest_data.py

build-indexes:
	uv run python scripts/build_bm25.py
	uv run python scripts/build_faiss.py

evaluate:
	uv run python scripts/evaluate.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
