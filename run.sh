#!/bin/bash
# Run the Edamam MCP Server (FastMCP)
#
# Set your credentials as environment variables before running:
#   export EDAMAM_APP_ID="your_app_id"
#   export EDAMAM_APP_KEY="your_app_key"
#
# Or use a .env file in the project root

# Check if credentials are set
if [ -z "$EDAMAM_APP_ID" ] || [ -z "$EDAMAM_APP_KEY" ]; then
    echo "Error: EDAMAM_APP_ID and EDAMAM_APP_KEY must be set"
    echo ""
    echo "Set them as environment variables:"
    echo "  export EDAMAM_APP_ID=\"your_app_id\""
    echo "  export EDAMAM_APP_KEY=\"your_app_key\""
    echo ""
    echo "Or create a .env file in the project root"
    exit 1
fi

echo "Starting Edamam MCP Server (FastMCP)..."
echo "Using EDAMAM_APP_ID: ${EDAMAM_APP_ID:0:8}..."
echo "Endpoint: http://localhost:8000/mcp/food-database/v1"
echo ""

# Run the FastMCP server
uv run python src/mcp_server.py
