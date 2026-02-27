# Migration Notes: FastAPI to FastMCP

## Overview

This document describes the migration from a custom FastAPI-based REST API to FastMCP with SSE transport.

## What Changed

### Architecture

**Before (FastAPI):**
```
app/
├── main.py                    # FastAPI application
├── routers/
│   ├── ai_router.py          # /v1/ai/query endpoint
│   ├── food_router.py        # Direct food endpoints
│   └── meta_router.py        # /v1/mcp/schema endpoint
├── services/
│   └── edamam_service.py     # Edamam API wrapper
└── utils/
    └── logger.py             # Logging utilities
```

**After (FastMCP):**
```
src/
├── mcp_server.py             # FastMCP server with 3 tools
├── edamam_service.py         # Refactored service layer
└── logger.py                 # Refactored logging
tests/
├── conftest.py               # Pytest fixtures
├── test_edamam_service.py    # Service tests
├── test_mcp_tools.py         # Tool tests
└── test_integration.py       # Integration tests
```

### Protocol Changes

| Aspect | Before (FastAPI) | After (FastMCP) |
|--------|-----------------|-----------------|
| Protocol | Custom REST API | MCP JSON-RPC 2.0 |
| Transport | HTTP | Streamable HTTP |
| Endpoints | Multiple REST endpoints | Single MCP server |
| Schema | OpenAI function format | MCP tool format |
| Discovery | `/v1/mcp/schema` endpoint | Built-in MCP protocol |

### Tool/Endpoint Mapping

#### 1. get_food_nutrition

**Before:**
```bash
POST /v1/ai/query
{
  "intent": "get_food_nutrition",
  "parameters": {
    "query": "banana",
    "quantity": 100
  }
}
```

**After:**
```python
# MCP tool call
get_food_nutrition(query="banana", quantity=100.0)
```

#### 2. search_food

**Before:**
```bash
POST /v1/ai/query
{
  "intent": "search_food",
  "parameters": {
    "query": "apple",
    "limit": 5
  }
}
```

**After:**
```python
# MCP tool call
search_food(query="apple", limit=5)
```

#### 3. analyze_food_image

**Before:**
```bash
POST /v1/ai/query
{
  "intent": "analyze_food_image",
  "parameters": {
    "image": "https://example.com/food.jpg"
  }
}
```

**After:**
```python
# MCP tool call
analyze_food_image(image_url="https://example.com/food.jpg")
```

Note: Parameter name changed from `image` to `image_url` for clarity.

## Breaking Changes

### 1. Server Startup

**Before:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**After:**
```bash
# SSE transport
uv run src/mcp_server.py

# stdio transport (for Claude Desktop)
uv run mcp run src/mcp_server.py
```

### 2. Client Integration

Clients must now use the MCP protocol instead of REST API calls.

**Before (REST):**
```python
import httpx

response = await httpx.post(
    "http://localhost:8000/v1/ai/query",
    json={
        "intent": "get_food_nutrition",
        "parameters": {"query": "banana", "quantity": 100}
    }
)
data = response.json()
```

**After (MCP):**
```python
from mcp import Client

async with Client("http://localhost:8000") as client:
    result = await client.call_tool(
        "get_food_nutrition",
        {"query": "banana", "quantity": 100.0}
    )
```

### 3. Schema Discovery

**Before:**
```bash
GET /v1/mcp/schema
# Returns OpenAI function definitions
```

**After:**
```python
# Built into MCP protocol
# Client calls list_tools() to discover available tools
tools = await client.list_tools()
```

### 4. Error Responses

**Before:**
```json
{
  "error": "Food not found",
  "status": 404
}
```

**After:**
```json
{
  "error": "Food not found",
  "query": "xyz",
  "message": "No matching food found in the database..."
}
```

Error responses now include more context and are part of the tool response (not HTTP status codes).

## What Stayed the Same

### ✅ Features Preserved

1. **UPC Detection**: Automatic detection of 8-14 digit barcodes
2. **Image URL Auto-detection**: Automatic redirect to image analysis
3. **Same Edamam API Integration**: All three core functions unchanged
4. **Request Logging**: File-based logging preserved
5. **Error Handling**: Graceful error handling maintained

### ✅ API Credentials

Environment variables remain the same:
```bash
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
```

### ✅ Response Formats

Response data structures are largely unchanged, just wrapped in MCP protocol.

## Migration Path for Clients

### Option 1: Update to MCP Protocol (Recommended)

Use a proper MCP client library:

1. Install an MCP client
2. Update connection to SSE transport
3. Replace REST calls with MCP tool calls
4. Update error handling for MCP responses

### Option 2: Bridge Layer

If you need to maintain REST API compatibility temporarily, create a bridge:

```python
# bridge.py - Example REST to MCP bridge
from fastapi import FastAPI
from mcp import Client

app = FastAPI()
mcp_client = Client("http://localhost:8000")

@app.post("/v1/ai/query")
async def query(request: dict):
    intent = request["intent"]
    params = request["parameters"]

    result = await mcp_client.call_tool(intent, params)
    return result
```

## Benefits of Migration

### Before (FastAPI)

- ~300 lines of routing code
- Custom schema generation
- Manual error handling
- No built-in MCP compliance
- HTTP-only transport

### After (FastMCP)

- ~100 lines of code (70% reduction)
- Automatic schema generation from type hints
- Built-in error handling
- True MCP protocol compliance
- Streamable HTTP transport for modern web hosting
- 99% test coverage

## Testing the Migration

### 1. Unit Tests

```bash
PYTHONPATH=. uv run pytest tests/ -v
# 54 tests, 99% coverage
```

### 2. MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run src/mcp_server.py
```

### 3. Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "edamam-food": {
      "command": "uv",
      "args": ["run", "/path/to/src/mcp_server.py"]
    }
  }
}
```

## Rollback Plan

If you need to rollback:

1. The old implementation remains in git history
2. Checkout the commit before migration:
   ```bash
   git log --oneline | grep "Before FastMCP"
   git checkout <commit-hash>
   ```

3. Or keep the old version in a separate branch:
   ```bash
   git checkout -b legacy-fastapi main~10
   ```

## Timeline

The migration was completed in phases:

1. **Phase 1**: Setup and dependencies
2. **Phase 2**: Service layer refactoring
3. **Phase 3**: FastMCP server implementation
4. **Phase 4**: Comprehensive testing
5. **Phase 5**: Documentation updates

Total effort: ~7 days of development

## Support

For migration questions or issues:
- Review the test files for usage examples
- Check the updated README.md
- Open an issue on GitHub
- Consult the FastMCP documentation
