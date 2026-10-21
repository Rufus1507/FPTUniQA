# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**University QA** is a RAG (Retrieval-Augmented Generation) system for Vietnamese university guidance, handling queries about academic regulations, tuition fees, scholarships, and enrollment procedures. It combines Hybrid Search (BM25 + FAISS), Cross-Encoder Reranking, Intent Classification, and LLM generation with citation tracing.

## Development Commands

This project uses **uv** for Python package management and virtual environments.

```bash
# Initial setup
make install          # or: uv venv && uv sync

# Development
make test            # Run all tests (uv run pytest tests/)
make test TEST_PATH=tests/unit/test_bm25.py  # Run single test file
make lint            # Check code quality (ruff)
make format          # Auto-format code (ruff format)

# Run services
make run-api        # FastAPI backend (http://localhost:8000/docs)
make run-frontend   # Streamlit UI (http://localhost:8501)

# Data pipeline
make ingest-data    # ETL: raw → processed corpus
make build-indexes  # Build BM25 + FAISS indexes
make evaluate       # Run evaluation benchmark

# Clean cache
make clean
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Query Processing                              │
│  QueryNormalizer → IntentClassifier (Factoid|Structured|OOD)       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌───────────────┐      ┌─────────────────┐      ┌──────────────┐
    │   Structured  │      │ Hybrid Retriever│      │     OOD      │
    │   Parser      │      │ (BM25 + FAISS) │      │   Rejection  │
    │ (tuition fees)│      │     + RRF       │      │              │
    └───────────────┘      └─────────────────┘      └──────────────┘
                                    │
                                    ▼
                         ┌─────────────────┐
                         │ Cross-Encoder   │
                         │ Reranker         │
                         └─────────────────┘
                                    │
                                    ▼
                         ┌─────────────────┐
                         │ Context Builder  │
                         │ + LLM Generation│
                         │ + Citation       │
                         └─────────────────┘
```

### Key Modules (`src/university_qa/`)

| Module | Responsibility |
|--------|----------------|
| `data/` | ETL pipeline: loader, cleaner, chunker (legal sections), metadata enrichment, structured data parser (tuition tables) |
| `retrieval/` | `bm25.py` (sparse), `dense.py`/embedding (FAISS), `rrf.py` (Reciprocal Rank Fusion), `retriever.py` (unified HybridRetriever) |
| `reranking/` | Cross-Encoder reranking (`bge-reranker-large`) for top-N refinement |
| `query/` | Query normalizer (abbreviations, normalization), intent classifier (keyword-based OOD/Factoid/Structured detection), query rewriting |
| `generation/` | LLM client (Gemini/OpenAI), prompt templates (anti-hallucination), context builder, citation extractor |
| `pipeline/` | `RAGPipeline` orchestrates the full flow; `ConversationalPipeline` handles multi-turn dialogue |
| `evaluation/` | Retrieval metrics (Hit@K, MRR, NDCG), answer faithfulness, hallucination detection |
| `utils/` | Config loader (YAML base + env override), JSONL I/O, structured logging |

### API (`api/`)

- `main.py`: FastAPI app with lifespan-managed RAG pipeline startup
- `routes/qa.py`: `POST /api/v1/query` — accepts `{query, top_k}`, returns `{answer, citations, retrieved_documents, intent}`
- `routes/health.py`: `GET /healthz`

### Frontend (`frontend/`)

Streamlit app that calls the backend API. Sample queries are predefined. Shows intent badge, answer, citations with doc_id references, and expandable retrieved document snippets.

## Configuration System

Configuration uses layered YAML files with environment override:

1. `configs/base.yaml` — base defaults (chunk sizes, model names, thresholds)
2. `configs/{environment}.yaml` — environment-specific overrides (loaded by `ENVIRONMENT` env var)
3. `.env` — API keys and runtime overrides

Key config sections:
- `data.raw_dir` / `data.processed_dir` — data paths
- `retrieval.bm25` / `retrieval.dense` — retrieval hyperparameters (top_k, k1, b, embedding model)
- `reranking` — enabled flag, model, top_n
- `generation` — provider (gemini/openai), model, temperature, system prompt

## Data Flow

```
data/raw/*.txt
    │
    ▼ scripts/ingest_data.py
data/processed/corpus.jsonl (cleaned, chunked, metadata-enriched)
    │
    ▼ scripts/build_bm25.py / build_faiss.py
data/processed/bm25_index/ + faiss_index/
    │
    ▼ RAGPipeline.load_corpus() at startup
Memory (in-memory index for retrieval)
```

## Key Patterns

- **Intent Classification**: Keyword-based regex matching in `query/intent.py`; OOD questions receive a rejection prompt to prevent hallucination
- **Hybrid Retrieval**: BM25 + Dense results merged via Reciprocal Rank Fusion (RRF) with configurable `k` parameter
- **Anti-Hallucination**: LLM receives strict system prompt + explicit instruction to cite source doc_ids; fallback rejection when OOD
- **Citation Extraction**: `generation/citation.py` matches answer spans against retrieved document chunks
- **Conversation Memory**: `pipeline/conversational_pipeline.py` maintains conversation history for follow-up queries
