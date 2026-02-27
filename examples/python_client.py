#!/usr/bin/env python3
"""
Example MCP Client for Edamam Food Database Server

A simple reference implementation showing how to interact with the MCP server.
"""

import asyncio
import httpx
from typing import Any, Dict, List, Optional


class MCPClient:
    """
    Simple MCP client for JSON-RPC 2.0 communication.

    Example usage:
        async with MCPClient("http://localhost:8000/mcp/food-database/v1") as client:
            await client.initialize("my-app", "1.0.0")
            tools = await client.list_tools()
            result = await client.call_tool("search_food", {"query": "banana"})
            print(result)
    """

    def __init__(self, endpoint: str, timeout: float = 30.0):
        """
        Initialize the MCP client.

        Args:
            endpoint: Full URL to the MCP endpoint
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.request_id = 0
        self.initialized = False
        self.server_info: Dict[str, Any] = {}
        self.capabilities: Dict[str, Any] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    def _next_id(self) -> int:
        """Generate next request ID."""
        self.request_id += 1
        return self.request_id

    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request.

        Args:
            method: JSON-RPC method name
            params: Method parameters (optional)

        Returns:
            Response result

        Raises:
            Exception: On protocol error or HTTP error
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with MCPClient()' pattern.")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method
        }

        if params is not None:
            request["params"] = params

        print(f"→ Sending: {method}")

        response = await self.client.post(self.endpoint, json=request)
        response.raise_for_status()

        data = response.json()

        # Check for JSON-RPC error
        if "error" in data:
            error = data["error"]
            raise Exception(f"JSON-RPC Error {error['code']}: {error['message']}")

        return data.get("result", {})

    async def initialize(self, client_name: str, client_version: str) -> Dict[str, Any]:
        """
        Initialize the MCP session.

        Must be called first before any other operations.

        Args:
            client_name: Name of your client application
            client_version: Version of your client

        Returns:
            Server initialization response
        """
        result = await self._send_request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": client_name,
                "version": client_version
            }
        })

        self.initialized = True
        self.server_info = result.get("serverInfo", {})
        self.capabilities = result.get("capabilities", {})

        print(f"✓ Initialized: {self.server_info.get('name')} v{self.server_info.get('version')}")
        return result

    async def ping(self) -> bool:
        """
        Send a ping to check if server is responsive.

        Returns:
            True if ping successful
        """
        await self._send_request("ping")
        print("✓ Ping successful")
        return True

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool definitions with schemas
        """
        if not self.initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        result = await self._send_request("tools/list", {})
        tools = result.get("tools", [])

        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

        return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool with the specified arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dict

        Returns:
            Tool result with content and isError flag

        Raises:
            Exception: If tool execution fails
        """
        if not self.initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        # Check if tool execution had an error
        if result.get("isError"):
            error_text = result.get("content", [{}])[0].get("text", "Unknown error")
            print(f"✗ Tool error: {error_text}")
        else:
            print(f"✓ Tool '{tool_name}' executed successfully")

        return result

    def get_tool_content(self, result: Dict[str, Any]) -> str:
        """
        Extract text content from tool result.

        Args:
            result: Tool call result

        Returns:
            Concatenated text content
        """
        content_items = result.get("content", [])
        text_parts = [item.get("text", "") for item in content_items if item.get("type") == "text"]
        return "\n".join(text_parts)


async def example_usage():
    """Example usage of the MCP client."""

    print("=" * 70)
    print("Edamam Food Database MCP Client Example")
    print("=" * 70)
    print()

    async with MCPClient("http://localhost:8000/mcp/food-database/v1") as client:
        # 1. Initialize
        print("Step 1: Initialize")
        await client.initialize("example-client", "1.0.0")
        print()

        # 2. Ping
        print("Step 2: Ping server")
        await client.ping()
        print()

        # 3. List tools
        print("Step 3: List available tools")
        tools = await client.list_tools()
        print()

        # 4. Search for a food
        print("Step 4: Search for 'banana'")
        result = await client.call_tool("search_food", {"query": "banana"})
        content = client.get_tool_content(result)
        print(content)
        print()

        # 5. Get detailed nutrition
        print("Step 5: Get nutrition for 150g banana")
        result = await client.call_tool("get_food_nutrition", {
            "query": "banana",
            "quantity": 150
        })
        content = client.get_tool_content(result)
        print(content[:500] + "..." if len(content) > 500 else content)
        print()

        # 6. Search by UPC code (example)
        print("Step 6: Search by UPC code")
        result = await client.call_tool("get_food_nutrition", {
            "query": "737628064502"
        })
        if result.get("isError"):
            print("(UPC lookup failed - may not be in database)")
        else:
            content = client.get_tool_content(result)
            print(content[:300] + "..." if len(content) > 300 else content)
        print()

        print("=" * 70)
        print("Example complete!")
        print("=" * 70)


async def interactive_mode():
    """Interactive mode - query foods interactively."""

    print("=" * 70)
    print("Interactive MCP Client")
    print("=" * 70)
    print()

    async with MCPClient("http://localhost:8000/mcp/food-database/v1") as client:
        await client.initialize("interactive-client", "1.0.0")
        print()

        while True:
            print("\nOptions:")
            print("1. Search food")
            print("2. Get nutrition")
            print("3. Analyze image")
            print("4. Quit")

            choice = input("\nChoice: ").strip()

            if choice == "1":
                query = input("Food name or UPC: ").strip()
                if query:
                    result = await client.call_tool("search_food", {"query": query})
                    print("\n" + client.get_tool_content(result))

            elif choice == "2":
                query = input("Food name or UPC: ").strip()
                quantity = input("Quantity in grams (default 100): ").strip()
                if query:
                    args = {"query": query}
                    if quantity:
                        args["quantity"] = float(quantity)
                    result = await client.call_tool("get_food_nutrition", args)
                    print("\n" + client.get_tool_content(result))

            elif choice == "3":
                url = input("Image URL: ").strip()
                if url:
                    result = await client.call_tool("analyze_food_image", {"image_url": url})
                    print("\n" + client.get_tool_content(result))

            elif choice == "4":
                print("Goodbye!")
                break


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(example_usage())
