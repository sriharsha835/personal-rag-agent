import httpx
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from db import engine

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_embedding = model.encode([query], normalize_embeddings=True)[0]
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, source, content, 1 - (embedding <=> (:qe)::vector) AS similarity
            FROM document_chunks ORDER BY embedding <=> (:qe)::vector LIMIT :k
        """), {"qe": str(query_embedding.tolist()), "k": top_k}).fetchall()
    return [{"id": r.id, "source": r.source, "content": r.content, "similarity": r.similarity} for r in rows]

def generate_answer(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{c['source']}]: {c['content']}" for c in chunks)
    prompt = f"""Answer the question using ONLY the context below. If it doesn't contain the answer, say so.

Context:
{context}

Question: {query}

Answer:"""
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=120.0)
    response.raise_for_status()
    return response.json()["response"]

def ask(query: str) -> str:
    return generate_answer(query, retrieve(query))

if __name__ == "__main__":
    question = input("Ask a question about your documents: ")
    print("\n" + ask(question))