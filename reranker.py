from sentence_transformers import CrossEncoder
from rag import retrieve, generate_answer

reranker_model = CrossEncoder("BAAI/bge-reranker-base")

def rerank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    pairs = [[query, c["content"]] for c in chunks]
    scores = reranker_model.predict(pairs)
    scored = sorted(zip(chunks, scores), key=lambda p: p[1], reverse=True)
    return [chunk for chunk, score in scored[:top_k]]

def ask_with_reranking(query: str) -> str:
    candidates = retrieve(query, top_k=10)
    top_chunks = rerank(query, candidates, top_k=3)
    return generate_answer(query, top_chunks)

if __name__ == "__main__":
    question = input("Ask a question (reranked retrieval): ")
    print("\n" + ask_with_reranking(question))