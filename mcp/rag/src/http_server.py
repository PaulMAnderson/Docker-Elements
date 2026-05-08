import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from pathlib import Path

from .rag_engine import RAGEngine
from .embeddings import EmbeddingClient
from .config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Code RAG Server", version="1.0.0")

# Global instances
rag_engine: Optional[RAGEngine] = None
embedding_client: Optional[EmbeddingClient] = None

# Pydantic models
class SearchRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    query: str
    limit: int = 10

class SearchResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    query: str
    results: List[dict]
    count: int

class IndexRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    paths: Optional[List[str]] = None

class IndexResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    indexed_repos: dict

@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on startup"""
    global rag_engine, embedding_client
    
    logger.info("Initializing HTTP Server components...")
    
    if not settings.requesty_api_key:
        logger.error("REQUESTY_API_KEY environment variable not set")
        raise RuntimeError("REQUESTY_API_KEY not configured")
    
    embedding_client = EmbeddingClient(
        settings.embedding_api_base_url,
        settings.embedding_model,
        settings.requesty_api_key,
        settings.embedding_batch_size
    )
    
    # Don't verify connection on startup - will fail on first actual use if API is down
    logger.info("Embedding client initialized (connection will be tested on first use)")
    
    rag_engine = RAGEngine(settings.db_path, embedding_client)
    
    logger.info("✓ HTTP Server ready")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_server": "ready" if rag_engine else "initializing",
        "embedding_model": settings.embedding_model,
        "api_endpoint": settings.embedding_api_base_url
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Search for relevant code chunks"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    results = rag_engine.search(request.query, request.limit)
    return SearchResponse(
        query=request.query,
        results=results,
        count=len(results)
    )

@app.post("/index", response_model=IndexResponse)
async def index(request: IndexRequest) -> IndexResponse:
    """Index code repositories"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    paths = request.paths or settings.code_paths
    
    all_results = {}
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            all_results[path_str] = {"error": "Path not found"}
            continue
        
        repo_name = path.name
        results = rag_engine.index_directory(path, repo_name)
        all_results[path_str] = results
    
    return IndexResponse(indexed_repos=all_results)

@app.get("/stats")
async def stats():
    """Get database statistics"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    return rag_engine.get_stats()

@app.get("/")
async def root():
    """API documentation"""
    return {
        "name": "Code RAG Server",
        "version": "1.0.0",
        "embedding_model": settings.embedding_model,
        "api_provider": "Requesty",
        "endpoints": {
            "health": "GET /health",
            "search": "POST /search",
            "index": "POST /index",
            "stats": "GET /stats"
        }
    }

def run_http_server():
    """Run HTTP server"""
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower()
    )