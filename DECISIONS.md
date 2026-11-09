@"
# Decisions

- Pinned the pgvector image to 0.8.7-pg16 (not the floating pg16 tag) so the database doesn't silently change over time.
- Bumped psycopg from 3.2.3 to 3.2.13: 3.2.3 has no prebuilt wheel for Python 3.14 on Windows.
- Bumped pydantic from 2.10.3 to 2.14.2: 2.10.3 has no wheel for Python 3.14 on Windows (it would need Rust and MSVC to compile).
- Using 127.0.0.1:55432 instead of localhost:5432: another Postgres on this machine (via WSL relay) answers on localhost, so 127.0.0.1 forces IPv4 and reaches the Docker container.
- Truncated document_chunks after switching to stable SHA-256 IDs, because intial built hash() rows were orphaned duplicates.
- One HNSW index only on the embedding column (no IVFFlat) to avoid planner picking the worse index.
- Kept langgraph 0.2.60 and langchain-core 0.3.28. They install cleanly on Python 3.14 and pass an import check.
- Chunk IDs are SHA-256 hashes of source and content, so re-running ingestion never duplicates rows (replaced hash()).
- Kept langgraph 0.2.60 and langchain-core 0.3.28 as planned: they install cleanly on Python 3.14 and pass an import check.
- Retrieval is separate from answer generation in each technique script, so later parts evals can plug in any technique.
- Reranking retrieves 10 candidates and keeps the top 3, because the cross-encoder is too slow to score everything.
- Router prompt lists the corpus topics because the 3B model otherwise sent document questions to direct. Must be kept in sync with the corpus.
- The direct path has its own prompt (3-sentence cap, 150 tokens, 180s timeout) because generate_answer is context-only and refuses when given no chunks.
- Renamed the LangGraph node route to router: a node cannot share a name with a state key.

## Observations (to revisit in later parts)

- CRAG graded a relevant chunk as weak for the 99.9 percent SLO question (grader false negative); the final answer was still correct.
- deep_retrieval shares a node with simple_retrieval, so multi-part questions underperform; decomposition.py answered the same question well. Candidate fix: route deep_retrieval to decomposition and evaluate it.
- Small-model quirks: RAG-Fusion produced a repeated and a drifting rephrasing; the Adaptive answer expanded SLO as Site Level Objective.
"@