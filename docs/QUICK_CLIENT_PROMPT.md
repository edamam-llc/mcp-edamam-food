# Quick MCP Client Prompt

Copy-paste this into a new conversation to quickly implement an MCP client:

---

I need an MCP client for the Edamam Food Database server.

**Server:** `POST http://localhost:8000/mcp/food-database/v1`
**Protocol:** JSON-RPC 2.0 (MCP spec 2025-03-26)

**Required sequence:**
1. `initialize` with protocolVersion "2025-03-26", capabilities {}, clientInfo
2. `tools/list` to get available tools
3. `tools/call` with tool name and arguments

**Three available tools:**
- `get_food_nutrition(query, quantity=100)` - Query can be food name, UPC code, or image URL
- `search_food(query, limit=5)` - Search for foods
- `analyze_food_image(image_url)` - Analyze food from image

**Example call:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_food",
    "arguments": {"query": "banana"}
  }
}
```

**Response format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{"type": "text", "text": "..."}],
    "isError": false
  }
}
```

**Implement:**
- Async HTTP client with JSON-RPC 2.0
- Initialize on first use
- Method to call any tool
- Parse content from results
- Handle errors (protocol errors in `.error`, tool errors in `result.isError`)

**Language:** [Your choice - Python, JavaScript, etc.]
**Style:** [Simple script / Full class / CLI tool / etc.]

Full spec: https://modelcontextprotocol.io/specification/2025-03-26/basic
