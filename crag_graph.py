import httpx
from typing import TypedDict
from langgraph.graph import StateGraph, END
from rag import retrieve, generate_answer

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

class CRAGState(TypedDict):
    question: str
    chunks: list[dict]
    relevance: str
    answer: str

def retrieve_node(state: CRAGState) -> CRAGState:
    return {**state, "chunks": retrieve(state["question"], top_k=5)}

def grade_node(state: CRAGState) -> CRAGState:
    context = "\n".join(c["content"][:200] for c in state["chunks"])
    prompt = f"""Does the context below contain enough information to answer the question?
Respond with ONLY one word: "relevant" or "weak".

Context: {context}
Question: {state['question']}

Answer:"""
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60.0)
    response.raise_for_status()
    verdict = response.json()["response"].strip().lower()
    return {**state, "relevance": "relevant" if "relevant" in verdict else "weak"}

def route_after_grading(state: CRAGState) -> str:
    return "generate" if state["relevance"] == "relevant" else "broaden_search"

def broaden_search_node(state: CRAGState) -> CRAGState:
    return {**state, "chunks": retrieve(state["question"], top_k=15)}

def generate_node(state: CRAGState) -> CRAGState:
    return {**state, "answer": generate_answer(state["question"], state["chunks"])}

def build_crag_graph():
    graph = StateGraph(CRAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("broaden_search", broaden_search_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grading, {"generate": "generate", "broaden_search": "broaden_search"})
    graph.add_edge("broaden_search", "generate")
    graph.add_edge("generate", END)
    return graph.compile()

# Built once at import time and reused — the graph itself is stateless, so rebuilding
# it on every call would work but wastes effort for no benefit.
_crag = build_crag_graph()

def retrieve_with_crag(query: str, top_k: int = 10) -> list[dict]:
    """Retrieval-only wrapper so CRAG can be plugged into a comparison script —
    the compiled graph's .invoke() returns the full state dict, not a chunk list."""
    result = _crag.invoke({"question": query, "chunks": [], "relevance": "", "answer": ""})
    return result["chunks"][:top_k]

if __name__ == "__main__":
    crag = _crag
    question = input("Ask a question (CRAG): ")
    result = crag.invoke({"question": question, "chunks": [], "relevance": "", "answer": ""})
    print(f"\nRelevance verdict: {result['relevance']}\n\nAnswer: {result['answer']}")