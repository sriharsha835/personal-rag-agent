import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from adaptive_rag_graph import build_adaptive_rag_graph

from db import engine  # imported so this module shares rag.py's pooled connection, not a second one
from rag import retrieve, generate_answer

app = FastAPI(title="personal-rag-agent")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    chunks = await asyncio.to_thread(retrieve, request.question)
    answer = await asyncio.to_thread(generate_answer, request.question, chunks)
    return QueryResponse(answer=answer, sources=list({c["source"] for c in chunks}))

_graph = None
_graph_lock = asyncio.Lock()

async def get_graph():
    global _graph
    if _graph is not None:
        return _graph
    async with _graph_lock:
        if _graph is None:  # re-check: another request may have built it while we waited
            _graph = await asyncio.to_thread(build_adaptive_rag_graph)
        return _graph

class AgentQueryResponse(BaseModel):
    route: str
    answer: str

@app.post("/agent-query", response_model=AgentQueryResponse)
async def agent_query(request: QueryRequest):
    graph = await get_graph()
    result = await asyncio.to_thread(graph.invoke, {"question": request.question, "route": "", "chunks": [], "relevance": "", "answer": ""})
    return AgentQueryResponse(route=result["route"], answer=result["answer"])