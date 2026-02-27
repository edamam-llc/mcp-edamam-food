# Edamam Food Database MCP Server

A **Model Context Protocol (MCP)** server for the Edamam Food Database API, implementing the official [MCP specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic) with full JSON-RPC 2.0 support.

## Features

- ✅ **Full MCP Protocol Compliance**: Implements JSON-RPC 2.0 specification
- ✅ **Single Endpoint**: `/mcp/food-database/v1` for all operations
- ✅ **Standard Methods**: `initialize`, `ping`, `tools/list`, `tools/call`
- ✅ **Three Tools**: Search foods, get nutrition, analyze food images
- ✅ **UPC/Barcode Support**: Automatically detects 8-14 digit codes
- ✅ **Image URL Auto-detection**: Seamlessly redirects image URLs
- ✅ **Proper Error Handling**: JSON-RPC error codes and tool execution errors
- ✅ **Capability Negotiation**: Full lifecycle management

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Edamam Food Database API credentials ([get them here](https://developer.edamam.com/))

### Installation

```bash
# Clone repository
git clone https://github.com/edamam/mcp-edamam-food.git
cd mcp-edamam-food

# Install dependencies
uv sync --extra dev

# Set credentials
export EDAMAM_APP_ID="your_app_id_here"
export EDAMAM_APP_KEY="your_app_key_here"

# Run server
./run.sh
```

The server will start on `http://localhost:8000/mcp/food-database/v1`

## MCP Protocol Implementation

### Endpoint

**Single endpoint for all operations:**
```
POST http://localhost:8000/mcp/food-database/v1
```

### JSON-RPC 2.0 Methods

#### 1. `initialize`

Initialize the MCP session and negotiate capabilities.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {
      "name": "your-client",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "edamam-food-database",
      "version": "2.0.0"
    },
    "instructions": "..."
  }
}
```

#### 2. `ping`

Health check to verify connection is alive.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "ping"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {}
}
```

#### 3. `tools/list`

List available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "tools": [
      {
        "name": "get_food_nutrition",
        "description": "Get detailed nutrition information...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "..."},
            "quantity": {"type": "number", "default": 100.0}
          },
          "required": ["query"]
        }
      },
      ...
    ]
  }
}
```

#### 4. `tools/call`

Execute a tool.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "search_food",
    "arguments": {
      "query": "banana"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "**Search Results for 'banana':**\n\n..."
      }
    ],
    "isError": false
  }
}
```

## Available Tools

### 1. get_food_nutrition

Get detailed nutrition information for a food item.

**Parameters:**
- `query` (string, required): Food name, UPC/barcode code, or image URL
- `quantity` (number, optional): Amount in grams (default: 100.0)

**Features:**
- Automatically detects UPC codes (8-14 digits)
- Auto-redirects image URLs to image analysis
- Returns comprehensive nutrition data

**Example:**
```json
{
  "name": "get_food_nutrition",
  "arguments": {
    "query": "banana",
    "quantity": 100
  }
}
```

### 2. search_food

Search for foods in the Edamam database.

**Parameters:**
- `query` (string, required): Food name or UPC/barcode code
- `limit` (integer, optional): Max results (default: 5)

**Features:**
- Handles UPC/barcode searches
- Returns foodId for detailed lookups
- Includes basic nutrition per 100g

**Example:**
```json
{
  "name": "search_food",
  "arguments": {
    "query": "apple"
  }
}
```

### 3. analyze_food_image

Analyze a food image and extract nutrition.

**Parameters:**
- `image_url` (string, required): URL of food image (HTTP/HTTPS)

**Features:**
- Detects ingredients from image
- Calculates total nutrition
- Uses Edamam's beta image API

**Example:**
```json
{
  "name": "analyze_food_image",
  "arguments": {
    "image_url": "https://example.com/salad.jpg"
  }
}
```

## Testing

### Manual Testing

Use the included test script:

```bash
chmod +x test_mcp.sh
./test_mcp.sh
```

### With curl

```bash
# 1. Initialize
curl -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0.0"}
    }
  }'

# 2. List tools
curl -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'

# 3. Call a tool
curl -X POST http://localhost:8000/mcp/food-database/v1 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_food",
      "arguments": {"query": "banana"}
    }
  }'
```

### With MCP Client

```python
import httpx
import json

BASE_URL = "http://localhost:8000/mcp/food-database/v1"

async def call_mcp(method, params=None, id=1):
    payload = {
        "jsonrpc": "2.0",
        "id": id,
        "method": method
    }
    if params:
        payload["params"] = params

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, json=payload)
        return response.json()

# Initialize
result = await call_mcp("initialize", {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {"name": "my-client", "version": "1.0.0"}
})

# List tools
tools = await call_mcp("tools/list")

# Call tool
nutrition = await call_mcp("tools/call", {
    "name": "get_food_nutrition",
    "arguments": {"query": "banana", "quantity": 100}
})
```

## Error Handling

The server implements proper JSON-RPC 2.0 error handling:

### Protocol Errors

Standard JSON-RPC error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC request |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Server error |

**Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: invalid_method"
  }
}
```

### Tool Execution Errors

Errors during tool execution are returned in the result with `isError: true`:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Failed to retrieve nutrition information: API timeout"
      }
    ],
    "isError": true
  }
}
```

## Architecture

### Protocol Flow

```
Client                      Server
  │                           │
  ├─ initialize ─────────────>│
  │<─ capabilities ───────────┤
  │                           │
  ├─ tools/list ─────────────>│
  │<─ tool schemas ───────────┤
  │                           │
  ├─ tools/call ─────────────>│
  │  (get_food_nutrition)     │
  │<─ nutrition data ─────────┤
  │                           │
  ├─ ping ───────────────────>│
  │<─ {} ─────────────────────┤
```

### Directory Structure

```
mcp-edamam-food/
├── src/
│   ├── mcp_server_v2.py      # MCP JSON-RPC 2.0 server
│   ├── edamam_service.py     # Edamam API service layer
│   └── logger.py             # Logging configuration
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── test_edamam_service.py
│   └── ...
├── logs/
│   └── mcp_requests.log      # Request logs
├── run.sh                    # Server startup script
├── test_mcp.sh               # MCP testing script
└── README.md
```

## Configuration

### Environment Variables

**Required:**
- `EDAMAM_APP_ID`: Your Edamam application ID
- `EDAMAM_APP_KEY`: Your Edamam API key

**Optional:**
- `LOG_LEVEL`: Logging level (default: INFO)

### Server Configuration

Edit `src/mcp_server_v2.py` to configure:
- `MCP_ENDPOINT`: API endpoint path
- `SERVER_NAME`: Server identifier
- `SERVER_VERSION`: Server version

## Logging

All requests are logged to `logs/mcp_requests.log`:

```
[2025-02-16 12:00:00] [INFO] Initialization request from test-client v1.0.0
[2025-02-16 12:00:01] [INFO] Server initialized successfully
[2025-02-16 12:00:02] [INFO] Tool call: search_food with args: {'query': 'banana'}
```

## Deployment

### Development

```bash
export EDAMAM_APP_ID="your_id"
export EDAMAM_APP_KEY="your_key"
./run.sh
```

### Production

Use a process manager like systemd:

```ini
[Unit]
Description=Edamam MCP Server
After=network.target

[Service]
Type=simple
User=mcp-user
WorkingDirectory=/path/to/mcp-edamam-food
Environment="EDAMAM_APP_ID=your_id"
Environment="EDAMAM_APP_KEY=your_key"
ExecStart=/usr/local/bin/uv run python src/mcp_server_v2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### With Docker

```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN pip install uv
COPY . .
RUN uv sync
EXPOSE 8000
CMD ["uv", "run", "python", "src/mcp_server_v2.py"]
```

## Specification Compliance

This server implements the [Model Context Protocol specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic):

- ✅ JSON-RPC 2.0 message format
- ✅ Lifecycle management (initialize/ping)
- ✅ Tool discovery (tools/list)
- ✅ Tool execution (tools/call)
- ✅ Proper error handling
- ✅ Capability negotiation

## Resources

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Edamam Food Database API](https://developer.edamam.com/food-database-api)

## Support

For issues and questions:
- Open an issue on GitHub
- Check the MCP specification
- Review the test files for usage examples

## License

See [LICENSE](LICENSE) file.
