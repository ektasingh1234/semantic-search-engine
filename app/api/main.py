import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from app.rag.rag_chain import ask

app = FastAPI(title="Semantic Search Engine")

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask_question(request: QueryRequest):
    result = ask(request.query)
    return {
        "query": request.query,
        "answer": result["answer"],
        "sources": result["sources"]
    }