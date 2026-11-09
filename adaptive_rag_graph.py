import httpx
from typing import TypedDict
from langgraph.graph import StateGraph, END
from rag import retrieve
from crag_graph import grade_node, route_after_grading, broaden_search_node, generate_node

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

class AdaptiveState(TypedDict):
    question: str
    route: str
    chunks: list[dict]
    relevance: str
    answer: str

def route_node(state: AdaptiveState) -> AdaptiveState:
    prompt = f"""You route questions for an assistant whose document collection covers:
site reliability engineering (SLOs, error budgets, incidents, postmortems), PostgreSQL indexing, Docker, and Python asyncio.

Choose exactly one category:
"simple_retrieval" = the question is about any topic those documents cover
"deep_retrieval" = the question has several parts or needs comparing different documents
"direct" = general knowledge clearly unrelated to those topics (for example geography, history, sports)

Respond with ONLY one of: simple_retrieval, deep_retrieval, direct

Question: {state['question']}

Category:"""
    response = httpx.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=120.0)
    response.raise_for_status()
    raw = response.json()["response"].strip().lower()
    print("RAW ROUTER OUTPUT:", repr(raw))   # temporary, remove after debugging
    route = next((r for r in ["deep_retrieval", "simple_retrieval", "direct"] if r in raw), "simple_retrieval")
    return {**state, "route": route}

def route_decision(state: AdaptiveState) -> str:
    return state["route"]

def direct_answer_node(state: AdaptiveState) -> AdaptiveState:
    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": f"Answer in at most 3 sentences.\n\nQuestion: {state['question']}",
            "stream": False,
            "options": {"num_predict": 150},
        },
        timeout=180.0,
    )
    response.raise_for_status()
    return {**state, "answer": response.json()["response"].strip()}

def simple_retrieve_node(state: AdaptiveState) -> AdaptiveState:
    return {**state, "chunks": retrieve(state["question"], top_k=5)}

def build_adaptive_rag_graph():
    graph = StateGraph(AdaptiveState)
    graph.add_node("router", route_node)
    graph.add_node("direct_answer", direct_answer_node)
    graph.add_node("simple_retrieve", simple_retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("broaden_search", broaden_search_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_decision, {
        "direct": "direct_answer", "simple_retrieval": "simple_retrieve", "deep_retrieval": "simple_retrieve",
    })
    graph.add_edge("direct_answer", END)
    graph.add_edge("simple_retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grading, {"generate": "generate", "broaden_search": "broaden_search"})
    graph.add_edge("broaden_search", "generate")
    graph.add_edge("generate", END)
    return graph.compile()

if __name__ == "__main__":
    adaptive_rag = build_adaptive_rag_graph()
    question = input("Ask a question (Adaptive RAG): ")
    result = adaptive_rag.invoke({"question": question, "route": "", "chunks": [], "relevance": "", "answer": ""})
    print(f"\nRoute chosen: {result['route']}\n\nAnswer: {result['answer']}")