# personal-rag-agent
# personal-rag-agent

A local, CPU-only, zero-cost RAG system built from scratch: ingestion, vector search, several advanced retrieval techniques, and (soon) an agentic pipeline, all measured against a fixed evaluation set.

> **Status:** Weeks 1-2 complete (baseline RAG, API, decomposition, HyDE, RAG-Fusion, reranking). Evaluation results and agentic RAG are in progress. Sections marked _TODO_ are filled in as each piece is built and measured.

![CI](https://github.com/sriharsha835/personal-rag-agent/actions/workflows/ci.yml/badge.svg) <!-- add once CI exists (Tier 3, Module F); remove until then -->

---

## 1. Problem

Language models don't know my documents and can confidently make things up. I wanted a retrieval-augmented system that answers from my own notes, runs entirely on a laptop with no GPU and no paid APIs, and can be **measured**, so that any claim like "technique X improves retrieval" is backed by a number.

## 2. Approach

1. Split documents into chunks and embed them with `BAAI/bge-small-en-v1.5` (384 dimensions).
2. Store them in Postgres + pgvector with a single HNSW index (cosine distance).
3. At question time, retrieve the closest chunks, put them in the prompt, and let a local model (`llama3.2:3b` via Ollama) answer only from that context.
4. Layer retrieval techniques on top and compare them on the same eval set.

## 3. Architecture

_TODO: embed `architecture.png` (Week 4, draw.io export)._

```
sample_docs/ -> ingest.py -> Postgres + pgvector (HNSW)
                                  |
question -> main.py (FastAPI) -> retrieval (baseline | decomposition | HyDE | fusion | rerank)
                                  |
                              Ollama (llama3.2:3b) -> answer
```

## 4. Retrieval techniques

Each runs on its own from the terminal. Retrieval is kept separate from generation so every technique can be plugged into the same eval script.

| Script | Idea | Cost |
|---|---|---|
| `rag.py` | Baseline: embed the question, nearest-neighbour search | 1 embedding |
| `decomposition.py` | LLM splits a multi-part question into sub-questions, retrieves for each, de-duplicates | extra LLM call |
| `hyde.py` | LLM writes a hypothetical answer; search with that instead of the raw question | extra LLM call |
| `rag_fusion.py` | LLM writes several rephrasings; results merged with Reciprocal Rank Fusion | extra LLM call + several searches |
| `reranker.py` | Retrieve 10 candidates, rescore with a cross-encoder (`bge-reranker-base`), keep top 3 | extra model pass |
| _CRAG / Adaptive RAG_ | _TODO (Week 3)_ | |

### Examples

The questions below are answerable from the files in `sample_docs/` (SRE, Postgres indexing, Docker, Python async). Outputs are from real runs on my machine; local-model wording varies slightly between runs.

**Baseline** (`python rag.py`)

```
Ask a question about your documents: What does an error budget mean?
An error budget is the amount of unreliability an SLO permits.
```

```
Ask a question about your documents: How much downtime does a 99.9 percent SLO allow per month?
A 99.9 percent SLO over a 30-day month allows roughly 43 minutes of downtime.
```

**Out-of-scope question** (`python rag.py`): the model should refuse, not guess.

```
Ask a question about your documents: Who won the 2018 World Cup?
There is no information in the provided context about the 2018 World Cup or any sports-related event.
```

**Decomposition** (`python decomposition.py`): a multi-part question gets split into sub-questions.

```
Ask a multi-part question: What is an error budget, and how does a B-tree index differ from a GIN index?
Sub-questions: ['What is an error budget?', 'What is the difference between B-tree and GIN indexes?', 'What is an error budget?']
```

The answer then covers both parts. The repeated sub-question is harmless: chunks are de-duplicated by ID before generation.

**HyDE** (`python hyde.py`)

```
Ask a question (HyDE retrieval): What does an error budget mean?
An error budget is the amount of unreliability an SLO (Service Level Objective) permits.
```

**RAG-Fusion** (`python rag_fusion.py`): the printed variations show what gets fused with RRF.

```
Ask a question (RAG-Fusion): What does an error budget mean?
Query variations: ['What does an error budget mean?', 'What is an error budget?', 'What does an error budget mean?', 'What is an error budget in statistics?', 'What is an error budget used for?']
```

Note the small model repeats one phrasing and drifts on another ("in statistics"). RRF tolerates this because chunks that appear across several lists still rise.

**Reranking** (`python reranker.py`)

```
Ask a question (reranked retrieval): How much downtime does a 99.9 percent SLO allow per month?
A 99.9 percent SLO allows roughly 43 minutes of downtime per month.
```

**API** (PowerShell; on macOS/Linux use `curl -X POST ... -H "Content-Type: application/json" -d '{...}'`)

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query -ContentType "application/json" -Body '{"question": "What does an error budget mean?"}'
```

> **Caveat:** with only four small documents, every technique retrieves nearly everything, so these examples show the code works, **not** that one technique beats another. The measured comparison is in [Results](#5-results).

## 5. Results

_TODO (Week 4). Fill this from real runs only._

Eval set: _N_ hand-labeled questions, version-controlled in `eval/`.

| Technique | Hit@3 | MRR | RAGAS (faithfulness / relevancy) | Avg latency |
|---|---|---|---|---|
| Baseline | | | | |
| Decomposition | | | | |
| HyDE | | | | |
| RAG-Fusion | | | | |
| Reranking | | | | |

### What worked / what didn't

_TODO: write this from the measured table, including techniques that did not help and why you think so._

## 6. How to run

**Prerequisites:** Python 3.11+, Docker, [Ollama](https://ollama.com) with `ollama pull llama3.2:3b`.

```bash
# 1. Database (pinned tag; see DECISIONS.md for why)
docker run -d --name pgvector-local -e POSTGRES_PASSWORD=postgres \
  -p 55432:5432 pgvector/pgvector:0.8.7-pg16

# 2. Environment
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: Copy-Item .env.example .env

# 3. Schema, then ingest
# macOS/Linux:  docker exec -i pgvector-local psql -U postgres -d postgres < schema.sql
# Windows:      Get-Content schema.sql | docker exec -i pgvector-local psql -U postgres -d postgres
python ingest.py

# 4. Ask questions
python rag.py                      # baseline
python rag_fusion.py               # or decomposition.py / hyde.py / reranker.py

# 5. API
uvicorn main:app --reload --port 8000
# http://127.0.0.1:8000/docs  (interactive)   /health   /query
```

Notes:
- First run downloads the embedding model (~130 MB); the reranker adds ~1 GB.
- Ollama must be running for decomposition, HyDE and fusion.
- Use `127.0.0.1`, not `localhost`, if another Postgres is installed on your machine. See `TROUBLESHOOTING.md`.

## 7. Design notes

- **One HNSW index only** on the embedding column. A second index type on the same column is wasteful and can mislead the query planner.
- **Idempotent ingestion:** chunk IDs are SHA-256 hashes, so re-running ingestion never duplicates rows.
- **Pinned versions** for the database image and Python dependencies, for reproducibility.
- **Local-only:** CPU, free models, no paid keys.

More in [`DECISIONS.md`](DECISIONS.md).

## 8. Limitations (honest list)

- Small corpus so far; technique comparisons are only meaningful on the Week 4 eval set.
- A 3B local model sometimes repeats or drifts when generating query variations; RRF tolerates this but it adds noise.
- Prompt-injection and bias risks are reviewed in _`BIAS_REFLECTION.md` (TODO, Tier 3 Module E)_.

## 9. Repo map

| Path | Purpose |
|---|---|
| `db.py` | Shared pooled SQLAlchemy engine |
| `schema.sql` | Table + single HNSW index |
| `ingest.py` | Chunk, embed, upsert (idempotent) |
| `rag.py` | Baseline retrieve + generate |
| `main.py` | FastAPI service |
| `decomposition.py`, `hyde.py`, `rag_fusion.py`, `reranker.py` | Retrieval techniques |
| `DECISIONS.md` | Why each non-obvious choice was made |
| `TROUBLESHOOTING.md` | Environment gotchas and fixes |

## License

MIT