@"
# Decisions

- Pinned the pgvector image to 0.8.7-pg16 (not the floating pg16 tag) so the database doesn't silently change over time.
- Bumped psycopg from 3.2.3 to 3.2.13: 3.2.3 has no prebuilt wheel for Python 3.14 on Windows.
- Bumped pydantic from 2.10.3 to 2.14.2: 2.10.3 has no wheel for Python 3.14 on Windows (it would need Rust and MSVC to compile).
- Using 127.0.0.1:55432 instead of localhost:5432: another Postgres on this machine (via WSL relay) answers on localhost, so 127.0.0.1 forces IPv4 and reaches the Docker container.
- Truncated document_chunks after switching to stable SHA-256 IDs, because intial built hash() rows were orphaned duplicates.
- One HNSW index only on the embedding column (no IVFFlat) to avoid planner picking the worse index.
- Kept langgraph 0.2.60 and langchain-core 0.3.28. They install cleanly on Python 3.14 and pass an import check.
"@