import httpx
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from db import engine
from rag import generate_answer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def generate_hypothetical_answer(query: str) -> str:
    prompt = f"Write a short, plausible-sounding paragraph that could answer this question, even if you're not sure it's correct:\n\n{query}"
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60.0)
    response.raise_for_status()
    return response.json()["response"]

def retrieve_with_hyde(query: str, top_k: int = 5) -> list[dict]:
    hypothetical = generate_hypothetical_answer(query)
    hyde_embedding = model.encode([hypothetical], normalize_embeddings=True)[0]
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, source, content, 1 - (embedding <=> (:qe)::vector) AS similarity
            FROM document_chunks ORDER BY embedding <=> (:qe)::vector LIMIT :k
        """), {"qe": str(hyde_embedding.tolist()), "k": top_k}).fetchall()
    return [{"id": r.id, "source": r.source, "content": r.content, "similarity": r.similarity} for r in rows]

def ask_with_hyde(query: str) -> str:
    return generate_answer(query, retrieve_with_hyde(query))

if __name__ == "__main__":
    question = input("Ask a question (HyDE retrieval): ")
    print("\n" + ask_with_hyde(question))