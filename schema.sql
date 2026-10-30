CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384)
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);