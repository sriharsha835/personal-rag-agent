import json, httpx
from rag import retrieve, generate_answer

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def generate_query_variations(query: str, n: int = 4) -> list[str]:
    prompt = f"""Generate {n} different phrasings of this search query, to improve retrieval.
Respond with ONLY a JSON array of {n} strings.

Original query: {query}

JSON array:"""
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60.0)
    response.raise_for_status()
    raw = response.json()["response"].strip()
    try:
        variations = json.loads(raw)
        if isinstance(variations, list):
            return [query] + variations
    except json.JSONDecodeError:
        pass
    return [query]

def reciprocal_rank_fusion(ranked_lists: list[list[dict]], k: int = 60) -> list[dict]:
    scores, chunk_by_id = {}, {}
    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list):
            chunk_by_id[chunk["id"]] = chunk
            scores[chunk["id"]] = scores.get(chunk["id"], 0.0) + 1.0 / (k + rank + 1)
    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [chunk_by_id[cid] for cid in sorted_ids]

def retrieve_with_rag_fusion(query: str, top_k: int = 5) -> list[dict]:
    """Retrieval-only half of RAG-Fusion — kept separate from generation so this
    can be plugged into a comparison script the same way rag.retrieve() is."""
    variations = generate_query_variations(query)
    print(f"Query variations: {variations}")
    ranked_lists = [retrieve(v, top_k=top_k) for v in variations]
    return reciprocal_rank_fusion(ranked_lists)[:top_k]

def ask_with_rag_fusion(query: str, top_k: int = 5) -> str:
    fused = retrieve_with_rag_fusion(query, top_k=top_k)
    return generate_answer(query, fused)

if __name__ == "__main__":
    question = input("Ask a question (RAG-Fusion): ")
    print("\n" + ask_with_rag_fusion(question))