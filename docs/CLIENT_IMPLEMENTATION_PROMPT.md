# MCP Client Implementation Prompt

Use this prompt in a new project/conversation to implement a client that uses the Edamam Food Database MCP Server.

---

## Prompt for AI Assistant

I need to implement a client that connects to an MCP (Model Context Protocol) server for the Edamam Food Database. The server implements the official MCP specification with JSON-RPC 2.0.

### Server Details

**Endpoint:** `POST http://localhost:8000/mcp/food-database/v1`
**Protocol:** JSON-RPC 2.0
**MCP Spec:** https://modelcontextprotocol.io/specification/2025-03-26/basic

### Required JSON-RPC Methods

#### 1. Initialize (Required First)

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
      "name": "my-client",
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

#### 2. List Tools

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_food_nutrition",
        "description": "Get detailed nutrition information for a food item...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Food name, UPC/barcode code, or image URL"
            },
            "quantity": {
              "type": "number",
              "description": "Amount in grams",
              "default": 100.0
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "search_food",
        "description": "Search for foods in the Edamam database...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Food name or UPC/barcode code"
            },
            "limit": {
              "type": "integer",
              "default": 5
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "analyze_food_image",
        "description": "Analyze a food image and extract nutrition...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "image_url": {
              "type": "string",
              "description": "URL of the food image",
              "format": "uri"
            }
          },
          "required": ["image_url"]
        }
      }
    ]
  }
}
```

#### 3. Call Tool

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
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
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "**Search Results for 'banana':**\n\nBanana, raw\n..."
      }
    ],
    "isError": false
  }
}
```

#### 4. Ping (Optional)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "ping"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {}
}
```

### Available Tools

**1. get_food_nutrition**
- Query: Food name, UPC code (8-14 digits), or image URL
- Quantity: Amount in grams (default: 100.0)
- Auto-detects UPC codes and image URLs
- Returns detailed nutrition information

**2. search_food**
- Query: Food name or UPC code
- Limit: Max results (default: 5)
- Returns list of foods with basic nutrition

**3. analyze_food_image**
- Image URL: HTTP/HTTPS URL of food photo
- Returns detected ingredients and nutrition

### Error Handling

**Protocol Errors:**
- Code -32700: Parse error
- Code -32600: Invalid request
- Code -32601: Method not found
- Code -32602: Invalid params
- Code -32603: Internal error

**Tool Execution Errors:**
- Result includes `isError: true`
- Error message in content

### Implementation Requirements

Please implement:

1. **MCP Client Class** that:
   - Manages the connection lifecycle
   - Handles JSON-RPC request/response
   - Tracks request IDs
   - Implements retry logic

2. **Initialization Flow**:
   - Call `initialize` first
   - Store server capabilities
   - Handle version negotiation

3. **Tool Discovery**:
   - Call `tools/list` after initialization
   - Parse and store tool schemas
   - Validate arguments against schemas

4. **Tool Execution**:
   - Method to call tools with arguments
   - Handle both success and error responses
   - Parse content from results

5. **Health Checks**:
   - Periodic ping requests
   - Connection timeout handling

### Example Use Cases

Implement these example flows:

**Example 1: Search and Get Nutrition**
```
1. initialize()
2. tools/list()
3. tools/call("search_food", {query: "banana"})
4. tools/call("get_food_nutrition", {query: "banana", quantity: 150})
```

**Example 2: UPC Lookup**
```
1. initialize()
2. tools/call("get_food_nutrition", {query: "737628064502"})
```

**Example 3: Image Analysis**
```
1. initialize()
2. tools/call("analyze_food_image", {image_url: "https://example.com/food.jpg"})
```

### Optional Features

Consider implementing:
- Connection pooling
- Request batching (JSON-RPC supports arrays)
- Caching of tool schemas
- Automatic retry on timeout
- Logging of all requests/responses

### Technology Suggestions

**Python:**
- Use `httpx` for async HTTP
- Use `pydantic` for JSON Schema validation
- Implement as async context manager

**JavaScript/TypeScript:**
- Use `axios` or `fetch` for HTTP
- Use `ajv` for JSON Schema validation
- Implement as class with Promise-based methods

**Other Languages:**
- Any HTTP client library
- JSON-RPC 2.0 support
- JSON Schema validation library

### Testing Checklist

Ensure your client:
- [ ] Successfully initializes with the server
- [ ] Can list all available tools
- [ ] Can call each tool successfully
- [ ] Handles protocol errors gracefully
- [ ] Handles tool execution errors gracefully
- [ ] Can make multiple sequential calls
- [ ] Validates arguments before sending
- [ ] Parses tool results correctly
- [ ] Handles network timeouts
- [ ] Logs requests/responses for debugging

### Expected Output Format

The client should expose a simple API like:

```python
# Python example
async with MCPClient("http://localhost:8000/mcp/food-database/v1") as client:
    # Initialize
    await client.initialize("my-app", "1.0.0")

    # Discover tools
    tools = await client.list_tools()

    # Call tool
    result = await client.call_tool("search_food", {"query": "banana"})
    print(result.content[0]["text"])
```

```javascript
// JavaScript example
const client = new MCPClient('http://localhost:8000/mcp/food-database/v1');

await client.initialize('my-app', '1.0.0');
const tools = await client.listTools();
const result = await client.callTool('search_food', { query: 'banana' });
console.log(result.content[0].text);
```

---

## Additional Context (Optional)

The server also provides:
- Health check: `GET /health`
- Server info: `GET /`
- Logs all requests to `logs/mcp_requests.log`

The server is designed to be stateless except for the initialization flag, so you can make requests from multiple clients simultaneously.
