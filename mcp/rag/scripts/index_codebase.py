#!/usr/bin/env python3
"""
Script to index codebase using Requesty API
Usage: python scripts/index_codebase.py [--paths path1,path2,...]
"""

import sys
import argparse
import logging
from pathlib import Path
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Index code repositories")
    parser.add_argument(
        "--paths",
        default="/mnt/code",
        help="Comma-separated paths to index"
    )
    parser.add_argument(
        "--api-url",
        default="https://router.requesty.ai/v1",
        help="Requesty API base URL"
    )
    parser.add_argument(
        "--model",
        default="vertex/google/text-embedding-005",
        help="Embedding model name"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("REQUESTY_API_KEY")
    if not api_key:
        logger.error("REQUESTY_API_KEY environment variable not set")
        sys.exit(1)
    
    # Import after args parsing to avoid issues
    from src.embeddings import EmbeddingClient
    from src.rag_engine import RAGEngine
    from src.config import settings
    
    paths = [p.strip() for p in args.paths.split(",")]
    
    try:
        logger.info(f"Initializing embedding client...")
        embedding_client = EmbeddingClient(
            args.api_url,
            args.model,
            api_key
        )
        
        # Verify connection
        if not embedding_client.verify_connection():
            logger.error("Failed to connect to Requesty API")
            sys.exit(1)
        
        logger.info(f"Initializing RAG engine...")
        rag_engine = RAGEngine(settings.db_path, embedding_client)
        
        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Path not found: {path_str}")
                continue
            
            logger.info(f"Indexing: {path}")
            results = rag_engine.index_directory(path, path.name)
            
            logger.info(f"Results for {path.name}:")
            logger.info(f"  Files processed: {results['files_processed']}")
            logger.info(f"  Chunks created: {results['chunks_created']}")
            logger.info(f"  Duration: {results['duration']:.2f}s")
        
        # Print final stats
        stats = rag_engine.get_stats()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total chunks: {stats.get('total_chunks', 0)}")
        logger.info(f"  Table: {stats.get('table_name')}")
        logger.info("\n✓ Indexing complete!")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()