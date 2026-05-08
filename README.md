# Agentic SWE System

An agentic software-engineering pipeline that takes a high-level coding task, retrieves relevant code context (AST chunks + call-graph expansion), generates a unified diff, hard-gates it through a schema-enforced reviewer, evaluates the result with deterministic tools (pytest/pylint/radon), and logs all runs to DuckDB for benchmarking and Pareto comparison across SOP (config) variants.

## Architecture decisions

| Decision | Reference system | This system | Why |
|---|---|---|---|
| Code chunking | Character-window splitting | AST-aware symbol-level chunks | Never splits mid-function/class; retrieval is unit-aligned to code semantics |
| Retrieval | Pure semantic similarity | Semantic + call-graph neighbor expansion | Captures structural relationships (callers/callees) not visible in embeddings |
| QA evaluation | LLM-as-a-Judge | Deterministic tool execution | Reproducible, auditable metrics (tests/lint/complexity) |
| SOP config | Runtime-generated JSON | Versioned YAML validated by Pydantic | Human-readable, diffable, swappable without code edits |
| Benchmark logging | In-memory dicts | DuckDB schema | Queryable live; supports A/B comparisons and evolution history |

## Benchmark results

See [benchmark_report.md](benchmark_report.md). (Fill this in once you’ve run the benchmark suite.)

## How to run

1. Create a virtualenv and install:

	- `pip install -e .`

2. Copy config:

	- `copy .env.example .env` (Windows) or `cp .env.example .env` (macOS/Linux)

3. Clone a target repo under `repos/` (e.g. httpie / rich / flask) and set `TEST_REPO_PATH` in `.env`.

4. Smoke run (once you’ve implemented agents):

	- `python -m src.graph --task "add docstrings to all undocumented functions" --sop sop/v1.0.yaml`

## Acknowledgements

This project adapts the architecture proposed in Fareed Khan’s “Building a Self-Improving Agentic RAG System” (Level Up Coding, Nov 2025). The SWE domain, AST chunker, call-graph retriever, deterministic QA metrics, DuckDB benchmark schema, and typed SOP mutation mechanism are implemented for this system.