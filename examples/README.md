# MCP Client Examples

Example implementations for connecting to the Edamam Food Database MCP Server.

## Python Client

A complete reference implementation in Python.

### Usage

**Basic example:**
```bash
# Ensure server is running first
cd ..
./run.sh

# In another terminal:
cd examples
uv run python python_client.py
```

**Interactive mode:**
```bash
uv run python python_client.py --interactive
```

### Features

- Full MCP lifecycle (initialize, ping)
- Tool discovery and execution
- Error handling
- Context manager pattern
- Interactive mode

### Key Methods

```python
async with MCPClient("http://localhost:8000/mcp/food-database/v1") as client:
    # Initialize session
    await client.initialize("my-app", "1.0.0")

    # Discover tools
    tools = await client.list_tools()

    # Call a tool
    result = await client.call_tool("search_food", {"query": "banana"})

    # Extract content
    text = client.get_tool_content(result)
```

## Creating Your Own Client

See the prompts in `/docs`:
- `CLIENT_IMPLEMENTATION_PROMPT.md` - Detailed guide
- `QUICK_CLIENT_PROMPT.md` - Quick reference

### Minimal Example

```python
import httpx

async def call_mcp(method, params=None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp/food-database/v1",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {}
            }
        )
        return response.json()

# Initialize
result = await call_mcp("initialize", {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0.0"}
})

# Call tool
result = await call_mcp("tools/call", {
    "name": "search_food",
    "arguments": {"query": "banana"}
})
```

## Other Languages

The same pattern works in any language with HTTP support:

- **JavaScript/TypeScript:** Use `fetch` or `axios`
- **Go:** Use `net/http`
- **Rust:** Use `reqwest`
- **Java:** Use `HttpClient`
- **C#:** Use `HttpClient`

The protocol is just JSON-RPC 2.0 over HTTP!
