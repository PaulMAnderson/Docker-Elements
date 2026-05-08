import lancedb
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import hashlib
from .embeddings import EmbeddingClient
from .config import settings

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, db_path: str, embedding_client: EmbeddingClient):
        self.db_path = db_path
        self.embedding_client = embedding_client
        self.db = lancedb.connect(db_path)
        self.table = None
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure the embeddings table exists"""
        try:
            self.table = self.db.open_table(settings.table_name)
            logger.info(f"Opened existing table: {settings.table_name}")
        except:
            logger.info(f"Creating new table: {settings.table_name}")
            # Create empty table with schema
            self.table = None
    
    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks"""
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else end
        
        return chunks if chunks else [""]
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content for change detection"""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def index_file(self, file_path: Path, repo_name: str = "") -> int:
        """Index a single file and return number of chunks added"""
        try:
            if not file_path.is_file():
                return 0
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if not content.strip():
                return 0
            
            # Get relative path for better readability
            rel_path = str(file_path.relative_to(Path("/mnt/code")) if Path("/mnt/code") in file_path.parents else file_path)
            file_hash = self._get_file_hash(file_path)
            
            # Check if file was already indexed
            if self.table is not None:
                try:
                    existing = self.table.search().where(
                        f"file_path = '{rel_path}' AND file_hash = '{file_hash}'"
                    ).limit(1).to_list()
                    if existing:
                        logger.debug(f"File already indexed: {rel_path}")
                        return 0
                except:
                    pass
            
            chunks = self._chunk_text(content)
            embeddings = self.embedding_client.embed_texts(chunks)
            
            documents = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is not None:
                    documents.append({
                        "chunk_id": f"{file_hash}_{i}",
                        "file_path": rel_path,
                        "file_hash": file_hash,
                        "repo_name": repo_name,
                        "chunk_index": i,
                        "content": chunk,
                        "embedding": embedding,
                        "indexed_at": datetime.now().isoformat(),
                        "file_size": len(content),
                        "chunk_count": len(chunks)
                    })
            
            if documents:
                if self.table is None:
                    self.table = self.db.create_table(settings.table_name, documents)
                else:
                    self.table.add(documents)
                logger.info(f"Indexed {len(documents)} chunks from {rel_path}")
                return len(documents)
            
            return 0
        
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return 0
    
    def index_directory(self, dir_path: Path, repo_name: str = "") -> dict:
        """Index all files in a directory"""
        results = {
            "files_processed": 0,
            "chunks_created": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in settings.exclude_dirs):
                    continue
                
                # Skip files without matching extensions
                if file_path.suffix.lower() not in settings.include_extensions:
                    continue
                
                chunks = self.index_file(file_path, repo_name)
                results["files_processed"] += 1
                results["chunks_created"] += chunks
        
        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
        
        return results
    
    def search(self, query: str, limit: int = 10) -> List[dict]:
        """Search for relevant code chunks"""
        if self.table is None:
            return []
        
        try:
            query_embedding = self.embedding_client.embed_text(query)
            if query_embedding is None:
                return []
            
            results = self.table.search(query_embedding).limit(limit).to_list()
            
            # Remove embedding from results for cleaner output
            for result in results:
                result.pop("embedding", None)
            
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        if self.table is None:
            return {"status": "empty"}
        
        try:
            count = self.table.count_rows()
            return {
                "total_chunks": count,
                "table_name": settings.table_name,
                "db_path": self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}