import json, httpx
from rag import retrieve, generate_answer

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def decompose_query(query: str) -> list[str]:
    prompt = f"""Break the question into 1-3 simpler sub-questions. If already simple, return it unchanged as the only item.
Respond with ONLY a JSON array of strings.

Question: {query}

JSON array:"""
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60.0)
    response.raise_for_status()
    raw = response.json()["response"].strip()
    try:
        sub_qs = json.loads(raw)
        if isinstance(sub_qs, list) and all(isinstance(q, str) for q in sub_qs):
            return sub_qs
    except json.JSONDecodeError:
        pass
    return [query]

def ask_with_decomposition(query: str) -> str:
    sub_questions = decompose_query(query)
    print(f"Sub-questions: {sub_questions}")
    all_chunks = []
    for sub_q in sub_questions:
        all_chunks.extend(retrieve(sub_q, top_k=3))
    seen, unique_chunks = set(), []
    for c in all_chunks:
        if c["id"] not in seen:
            seen.add(c["id"]); unique_chunks.append(c)
    return generate_answer(query, unique_chunks)

if __name__ == "__main__":
    question = input("Ask a multi-part question: ")
    print("\n" + ask_with_decomposition(question))