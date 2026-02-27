#!/bin/bash
# Test script for MCP JSON-RPC 2.0 server

# Set credentials
export EDAMAM_APP_ID="5ca47152"
export EDAMAM_APP_KEY="26c1dedff4b41dcb4c38f0c194fb6e88"

# Start server in background
./run.sh > /tmp/mcp_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "Testing MCP JSON-RPC 2.0 Server"
echo "================================"
echo ""

# Test 1: Ping
echo "Test 1: Ping"
curl -s -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
echo -e "\n"

# Test 2: Initialize
echo "Test 2: Initialize"
curl -s -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'
echo -e "\n"

# Test 3: List tools
echo "Test 3: List Tools"
curl -s -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}'
echo -e "\n"

# Test 4: Search food
echo "Test 4: Search Food (banana)"
curl -s -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search_food","arguments":{"query":"banana"}}}'
echo -e "\n"

# Cleanup
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null

echo "Tests complete!"
