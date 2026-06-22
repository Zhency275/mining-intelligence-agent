"""MCP Client Manager — Manages connections to all 3 MCP servers via stdio.

This module handles:
- Starting MCP server subprocesses
- Initializing MCP sessions
- Discovering tools from each server
- Routing tool calls to the correct server
- Graceful shutdown of all connections

Uses contextlib.AsyncExitStack for proper async context manager lifecycle.
"""

import asyncio
import json
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to project root (for resolving server module paths)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""
    name: str
    module: str  # e.g. "server_a_mine_production.server"


@dataclass
class ToolInfo:
    """Metadata about a discovered tool."""
    name: str
    description: str
    input_schema: dict
    server_name: str


@dataclass
class MCPClientManager:
    """Manages connections to multiple MCP servers and provides tool routing."""

    servers: list[ServerConfig] = field(default_factory=lambda: [
        ServerConfig(name="mine_production", module="server_a_mine_production.server"),
        ServerConfig(name="commodity_price", module="server_b_commodity_price.server"),
        ServerConfig(name="mining_news", module="server_c_mining_news.server"),
    ])

    # Internal state
    _exit_stack: AsyncExitStack | None = None
    _sessions: dict[str, ClientSession] = field(default_factory=dict)
    _tools: list[ToolInfo] = field(default_factory=list)

    async def start_all(self) -> list[ToolInfo]:
        """Start all MCP servers and discover their tools."""
        self._exit_stack = AsyncExitStack()
        self._tools = []
        self._sessions = {}

        for server_config in self.servers:
            print(f"[MCPManager] Starting {server_config.name}...", file=sys.stderr)
            try:
                tools = await self._start_server(server_config)
                self._tools.extend(tools)
                print(f"[MCPManager] {server_config.name}: {len(tools)} tools discovered", file=sys.stderr)
            except Exception as e:
                print(f"[MCPManager] ERROR starting {server_config.name}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                # Continue with remaining servers even if one fails
                continue

        print(f"[MCPManager] Total tools available: {len(self._tools)}", file=sys.stderr)
        return self._tools

    async def _start_server(self, config: ServerConfig) -> list[ToolInfo]:
        """Start a single MCP server subprocess and discover its tools."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", config.module],
        )

        # Use AsyncExitStack to properly manage async context lifecycle
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()

        # Discover tools
        result = await session.list_tools()
        tools = []
        for tool in result.tools:
            tools.append(ToolInfo(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                server_name=config.name,
            ))

        self._sessions[config.name] = session
        return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Route a tool call to the correct MCP server and return the result."""
        # Find which server owns this tool
        tool_info = None
        for t in self._tools:
            if t.name == tool_name:
                tool_info = t
                break

        if not tool_info:
            return json.dumps({"error": f"Tool not found: {tool_name}"})

        session = self._sessions.get(tool_info.server_name)
        if not session:
            return json.dumps({"error": f"Server not connected: {tool_info.server_name}"})

        try:
            result = await session.call_tool(tool_name, arguments)
            # MCP returns content as a list of content blocks
            if result.content:
                for block in result.content:
                    if hasattr(block, 'text') and block.text:
                        return block.text
                    elif hasattr(block, 'data'):
                        return str(block.data)
                return str(result.content[0])
            return json.dumps({"result": "success", "note": "no content returned"})
        except Exception as e:
            return json.dumps({"error": f"Tool call failed: {str(e)}"})

    def get_tools_schema(self) -> list[dict]:
        """Return tools in Anthropic API compatible format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools
        ]

    def get_tool_names_by_server(self) -> dict[str, list[str]]:
        """Return a mapping of server name -> list of tool names."""
        mapping: dict[str, list[str]] = {}
        for t in self._tools:
            mapping.setdefault(t.server_name, []).append(t.name)
        return mapping

    async def shutdown(self) -> None:
        """Gracefully shut down all MCP server connections via AsyncExitStack."""
        if self._exit_stack:
            print("[MCPManager] Shutting down all servers...", file=sys.stderr)
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                print(f"[MCPManager] Error during shutdown: {e}", file=sys.stderr)
        self._sessions.clear()
        self._tools.clear()
        print("[MCPManager] All servers shut down.", file=sys.stderr)


# Simple test to verify connections
async def test_connections():
    """Test that all MCP servers can start and respond."""
    manager = MCPClientManager()
    try:
        tools = await manager.start_all()
        print(f"\nDiscovered {len(tools)} tools:")
        for tool in tools:
            print(f"  [{tool.server_name}] {tool.name}: {tool.description[:80]}...")

        # Test a simple call
        print("\n--- Testing get_mine_overview('Pilgangoora') ---")
        result = await manager.call_tool("get_mine_overview", {"mine_name": "Pilgangoora"})
        print(result[:500])
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(test_connections())
