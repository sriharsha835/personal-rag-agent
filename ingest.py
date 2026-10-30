import glob
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from db import engine

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def chunk_text(text_content: str, chunk_size: int = 500) -> list[str]:
    words = text_content.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def ingest_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    chunks = chunk_text(content)
    embeddings = model.encode(chunks, normalize_embeddings=True)
    with engine.connect() as conn:
        for chunk, embedding in zip(chunks, embeddings):
            conn.execute(text("""
                INSERT INTO document_chunks (id, source, content, embedding)
                VALUES (:id, :source, :content, (:embedding)::vector)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
            """), {
                "id": f"{filepath}::{hash(chunk)}",  # fixed properly on Day 3
                "source": filepath, "content": chunk,
                "embedding": str(embedding.tolist()),
            })
        conn.commit()
    print(f"Ingested {len(chunks)} chunks from {filepath}")

if __name__ == "__main__":
    for filepath in glob.glob("sample_docs/*.txt"):
        ingest_file(filepath)