import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

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