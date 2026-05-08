"""Custom RAG MCP server for code retrieval"""

import sys
import logging
from pathlib import Path

from mcp.server import Server
from mcp.types import TextContent

from .embeddings import EmbeddingClient
from .rag_engine import RAGEngine
from .config import settings

# Setup logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global state
embedding_client: EmbeddingClient | None = None
rag_engine: RAGEngine | None = None

# Create server
server = Server("code-rag-server")


def init_rag():
    """Initialize RAG components"""
    global embedding_client, rag_engine
    
    if not settings.requesty_api_key:
        raise RuntimeError("REQUESTY_API_KEY not set")
    
    logger.info("Initializing RAG engine...")
    embedding_client = EmbeddingClient(
        settings.embedding_api_base_url,
        settings.embedding_model,
        settings.requesty_api_key,
        settings.embedding_batch_size
    )
    
    rag_engine = RAGEngine(settings.db_path, embedding_client)
    logger.info("✓ RAG engine initialized")


@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        {
            "name": "search_codebase",
            "description": "Search the codebase using vector similarity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10}
                },
                "required": ["query"]
            }
        },
        {
            "name": "index_codebase",
            "description": "Index code repositories",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "paths": {"type": "string", "description": "Comma-separated paths"}
                }
            }
        },
        {
            "name": "get_database_stats",
            "description": "Get database statistics",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "get_file_chunks",
            "description": "Get all chunks from a file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "File name"}
                },
                "required": ["filename"]
            }
        }
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "search_codebase":
            return await handle_search(arguments)
        elif name == "index_codebase":
            return await handle_index(arguments)
        elif name == "get_database_stats":
            return await handle_stats(arguments)
        elif name == "get_file_chunks":
            return await handle_get_chunks(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_search(arguments: dict) -> list[TextContent]:
    if rag_engine is None:
        return [TextContent(type="text", text="RAG engine not initialized")]
    
    query = arguments.get("query", "")
    limit = arguments.get("limit", 10)
    
    results = rag_engine.search(query, limit)
    if not results:
        return [TextContent(type="text", text=f"No results for: {query}")]
    
    output = []
    for i, result in enumerate(results, 1):
        text = f"Result {i}:\nFile: {result.get('file_path')}\n"
        text += f"Chunk {result.get('chunk_index', 0) + 1}/{result.get('chunk_count', 1)}\n"
        text += f"---\n{result.get('content')}\n"
        output.append(TextContent(type="text", text=text))
    
    return output


async def handle_index(arguments: dict) -> list[TextContent]:
    if rag_engine is None:
        return [TextContent(type="text", text="RAG engine not initialized")]
    
    paths_str = arguments.get("paths", "")
    if paths_str:
        index_paths = [p.strip() for p in paths_str.split(",")]
    else:
        index_paths = settings.code_paths
    
    text = "Indexing Results:\n\n"
    
    for path_str in index_paths:
        path = Path(path_str)
        if not path.exists():
            text += f"❌ Not found: {path_str}\n"
            continue
        
        text += f"📁 Indexing: {path_str}\n"
        results = rag_engine.index_directory(path, path.name)
        text += f"  Files: {results['files_processed']}\n"
        text += f"  Chunks: {results['chunks_created']}\n"
        text += f"  Time: {results['duration']:.2f}s\n\n"
    
    stats = rag_engine.get_stats()
    text += f"Total chunks: {stats.get('total_chunks', 0)}\n"
    
    return [TextContent(type="text", text=text)]


async def handle_stats(arguments: dict) -> list[TextContent]:
    if rag_engine is None:
        return [TextContent(type="text", text="RAG engine not initialized")]
    
    stats = rag_engine.get_stats()
    text = f"Total chunks: {stats.get('total_chunks', 0)}\n"
    text += f"Table: {stats.get('table_name')}\n"
    text += f"Location: {stats.get('db_path')}\n"
    
    return [TextContent(type="text", text=text)]


async def handle_get_chunks(arguments: dict) -> list[TextContent]:
    if rag_engine is None or rag_engine.table is None:
        return [TextContent(type="text", text="Database not initialized")]
    
    filename = arguments.get("filename", "")
    results = rag_engine.table.search().where(
        f"file_path LIKE '%{filename}%'"
    ).to_list()
    
    if not results:
        return [TextContent(type="text", text=f"No chunks for: {filename}")]
    
    chunks_by_index = sorted(results, key=lambda x: x.get('chunk_index', 0))
    text = f"File: {filename}\nChunks: {len(chunks_by_index)}\n---\n\n"
    
    for chunk in chunks_by_index:
        text += f"Chunk {chunk.get('chunk_index', 0) + 1}:\n"
        text += f"{chunk.get('content')}\n\n---\n\n"
    
    return [TextContent(type="text", text=text)]


def run_stdio_server():
    """Run the MCP server using stdio"""
    try:
        init_rag()
        logger.info("✓ MCP STDIO server starting...")
        
        # Import here to avoid issues
        import subprocess
        import sys as sys_module
        
        # Run the server in a subprocess with proper event loop
        from mcp.server import stdio_server
        stdio_server(server).run()
        
    except KeyboardInterrupt:
        logger.info("MCP server stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_stdio_server()