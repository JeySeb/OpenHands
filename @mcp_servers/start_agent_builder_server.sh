#!/bin/bash

# Agent Builder MCP Server Startup Script
# This script configures and starts the Agent Builder MCP Server for OpenHands integration

set -e

# Default configuration
DEFAULT_PORT=8001
DEFAULT_HOST="127.0.0.1"
DEFAULT_BASE_URL="http://localhost:8000"
DEFAULT_TRANSPORT="streamable-http"

# Parse command line arguments
SHOW_HELP=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --token)
            API_TOKEN="$2"
            shift 2
            ;;
        --transport)
            TRANSPORT="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show help
if [ "$SHOW_HELP" = true ]; then
    cat << EOF
Agent Builder MCP Server Startup Script

Usage: $0 [OPTIONS]

OPTIONS:
    --port PORT         Port to run the MCP server on (default: $DEFAULT_PORT)
    --host HOST         Host to bind the server to (default: $DEFAULT_HOST)
    --base-url URL      Base URL of the Agent Builder Backend API (default: $DEFAULT_BASE_URL)
    --token TOKEN       Authentication token for the backend API
    --transport TYPE    Transport type: stdio, http, or streamable-http (default: $DEFAULT_TRANSPORT)
    --help, -h          Show this help message

ENVIRONMENT VARIABLES:
    AGENT_BUILDER_API_TOKEN      - Authentication token (overrides --token)
    AGENT_BUILDER_API_BASE_URL   - Backend API base URL (overrides --base-url)
    MCP_HTTP_HOST               - Server host (overrides --host)
    MCP_HTTP_PORT               - Server port (overrides --port)
    MCP_TRANSPORT               - Transport type (overrides --transport)

EXAMPLES:
    # Start with default settings
    $0

    # Start on custom port with specific backend
    $0 --port 8002 --base-url http://api.example.com --token your-token

    # Start with stdio transport (for OpenHands direct integration)
    $0 --transport stdio

    # Start for production with environment variables
    export AGENT_BUILDER_API_TOKEN="your-production-token"
    export AGENT_BUILDER_API_BASE_URL="https://api.production.com"
    $0 --port 8001

EOF
    exit 0
fi

# Set environment variables with defaults
export MCP_HTTP_HOST="${HOST:-$DEFAULT_HOST}"
export MCP_HTTP_PORT="${PORT:-$DEFAULT_PORT}"
export AGENT_BUILDER_API_BASE_URL="${BASE_URL:-$DEFAULT_BASE_URL}"
export MCP_TRANSPORT="${TRANSPORT:-$DEFAULT_TRANSPORT}"

# Set token if provided
if [ -n "$API_TOKEN" ]; then
    export AGENT_BUILDER_API_TOKEN="$API_TOKEN"
fi

# Check if token is set
if [ -z "$AGENT_BUILDER_API_TOKEN" ]; then
    echo "⚠️  WARNING: AGENT_BUILDER_API_TOKEN not set"
    echo "   The server will use the default token 'your-api-token-here'"
    echo "   Set the token using --token or the AGENT_BUILDER_API_TOKEN environment variable"
    echo ""
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_PATH="$SCRIPT_DIR/agent_builder_mcp.py"

# Verify the MCP server file exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo "❌ Error: MCP server file not found at $MCP_SERVER_PATH"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    echo "   Please install Python 3.7+ to run the MCP server"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Display configuration
echo "🚀 Starting Agent Builder MCP Server"
echo "=================================="
echo "Host:                $MCP_HTTP_HOST"
echo "Port:                $MCP_HTTP_PORT"
echo "Transport:           $MCP_TRANSPORT"
echo "Backend API URL:     $AGENT_BUILDER_API_BASE_URL"
echo "Token Set:           $([ -n "$AGENT_BUILDER_API_TOKEN" ] && echo "✅ Yes" || echo "❌ No")"
echo "Server Path:         $MCP_SERVER_PATH"
echo "Python Command:      $PYTHON_CMD"
echo "=================================="
echo ""

# Start the server
echo "🔄 Starting server..."
if [ "$MCP_TRANSPORT" = "stdio" ]; then
    echo "📡 Running in stdio mode (suitable for direct OpenHands integration)"
else
    echo "🌐 Running in HTTP mode at http://$MCP_HTTP_HOST:$MCP_HTTP_PORT"
    echo ""
    echo "🔗 To use with OpenHands, add this to your config.toml:"
    echo ""
    echo "[mcp]"
    echo "shttp_servers = ["
    echo "    {url=\"http://$MCP_HTTP_HOST:$MCP_HTTP_PORT/mcp\", api_key=\"\"}"
    echo "]"
    echo ""
fi

# Execute the MCP server
exec "$PYTHON_CMD" "$MCP_SERVER_PATH" ${PORT:+--port "$PORT"}
