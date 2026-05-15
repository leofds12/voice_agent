import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import MCP_SERVER_PATH

class MCPClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.exit_stack = AsyncExitStack()
        self.session = None
        self._connected = False

    async def connect(self):
        server_params = StdioServerParameters(
            command="python",
            args=[MCP_SERVER_PATH, self.db_path],
        )
        transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport
        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self.session = session
        self._connected = True
        print("MCP SQL Server conectado.")

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Llama a una herramienta del servidor MCP y retorna el texto del resultado."""
        if not self._connected or not self.session:
            raise RuntimeError("MCP Client no conectado.")
        result = await self.session.call_tool(tool_name, arguments)
        # El contenido viene como lista de objetos con .text
        return result.content[0].text

    async def close(self):
        await self.exit_stack.aclose()
        self._connected = False