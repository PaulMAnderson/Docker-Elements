#!/bin/bash

set -e

cd /app
mkdir -p /var/log/rag-server

# Set defaults
HTTP_PORT=${HTTP_PORT:-8000}
HTTP_HOST=${HTTP_HOST:-0.0.0.0}
START_MODE=${START_MODE:-http-only}
LOG_LEVEL=${LOG_LEVEL:-info}

{
    echo "=== RAG MCP Server Starting at $(date) ==="
    echo "Configuration:"
    echo "  API Base URL: $EMBEDDING_API_BASE_URL"
    echo "  Embedding Model: $EMBEDDING_MODEL"
    echo "  DB Path: $DB_PATH"
    echo "  HTTP Port: $HTTP_PORT"
    echo "  HTTP Host: $HTTP_HOST"
    echo "  Start Mode: $START_MODE"
    echo "========================================"
    
    if [ -z "$REQUESTY_API_KEY" ]; then
        echo "✗ ERROR: REQUESTY_API_KEY not set"
        exit 1
    fi
    
    if [ "$START_MODE" = "http-only" ]; then
        echo "✓ Starting HTTP server only on ${HTTP_HOST}:${HTTP_PORT}..."
        python -m uvicorn src.http_server:app \
            --host "$HTTP_HOST" \
            --port "$HTTP_PORT" \
            --log-level "$LOG_LEVEL"
    
    elif [ "$START_MODE" = "stdio-only" ]; then
        echo "✓ Starting MCP STDIO server only..."
        python -m src.mcp_server
    
    else
        # START_MODE = both
        echo "✓ Starting both HTTP (${HTTP_HOST}:${HTTP_PORT}) and MCP STDIO servers..."
        
        # Start HTTP server in background
        python -m uvicorn src.http_server:app \
            --host "$HTTP_HOST" \
            --port "$HTTP_PORT" \
            --log-level "$LOG_LEVEL" > /var/log/rag-server/http.log 2>&1 &
        HTTP_PID=$!
        
        echo "✓ HTTP server started (PID: $HTTP_PID)"
        sleep 2
        
        # Start MCP STDIO server in foreground
        python -m src.mcp_server
        
        # Cleanup
        kill $HTTP_PID 2>/dev/null || true
    fi
    
} 2>&1 | tee -a /var/log/rag-server/server.log