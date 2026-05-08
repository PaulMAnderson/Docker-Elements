from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os

class Settings(BaseSettings):
    # Embedding Model
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "vertex/google/text-embedding-005")
    embedding_api_base_url: str = os.getenv("EMBEDDING_API_BASE_URL", "https://router.requesty.ai/v1")
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    requesty_api_key: str = os.getenv("REQUESTY_API_KEY", "")
    
    # Database
    db_path: str = os.getenv("DB_PATH", "/data/lancedb")
    table_name: str = os.getenv("TABLE_NAME", "code_embeddings")
    
    # Code paths
    code_paths: list[str] = ["/mnt/code"]
    
    # File patterns to index
    include_extensions: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".cpp", ".c",
        ".h", ".hpp", ".cs", ".rb", ".php",
        ".swift", ".kt", ".scala", ".r",
        ".sql", ".json", ".yaml", ".yml",
        ".md", ".txt"
    ]
    
    exclude_dirs: set[str] = {
        ".git", ".venv", "venv", "node_modules",
        "__pycache__", ".pytest_cache", "dist",
        "build", ".egg-info", ".tox", "coverage"
    }
    
    # Chunk settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # Server settings
    http_port: int = int(os.getenv("HTTP_PORT", "8000"))
    http_host: str = os.getenv("HTTP_HOST", "0.0.0.0")
    
    # MCP settings
    mcp_enabled: bool = os.getenv("MCP_ENABLED", "true").lower() == "true"
    http_enabled: bool = os.getenv("HTTP_ENABLED", "true").lower() == "true"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")
    log_file: str = os.getenv("LOG_FILE", "/var/log/rag-server/server.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()