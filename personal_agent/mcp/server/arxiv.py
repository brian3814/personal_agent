import os
from contextlib import AsyncExitStack
from typing import Optional

from fastmcp.utilities.logging import get_logger
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset, 
    StdioConnectionParams,
    StdioServerParameters
)

logger = get_logger(__name__)

def print_stdout(proc):
    for line in iter(proc.stdout.readline, ''):
        if not line:
            break
        print("[SERVER STDOUT]", line, end='')


class ArxivMCPServerManager:    
    def __init__(
        self, 
        *, 
        storage_path: Optional[str] = None
    ):
        self.storage_path = storage_path or os.path.expanduser("~/.arxiv-mcp-server/papers")
        self.client = None
        self.read_stream = None
        self.write_stream = None
        self.session: ClientSession = None
        self.exit_stack = AsyncExitStack()

    def get_toolset(self):
        toolset = MCPToolset(connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='uv',
                args=[
                    'tool',
                    'run',
                    'arxiv-mcp-server',
                    '--storage-path', self.storage_path
                ],
            )
        ))

        self.toolset = toolset

        return self.toolset

    async def get_session(self):
        if self.session:
            return
        
        stdio_params = StdioServerParameters(
            command='uv',
            args=[
                'tool',
                'run',
                'arxiv-mcp-server',
                '--storage-path', self.storage_path
            ],
        )

        self.client = stdio_client(stdio_params)
        self.read_stream, self.write_stream = await self.exit_stack.enter_async_context(self.client)
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.read_stream, self.write_stream)
        )

        await self.session.initialize()

    async def shutdown(self):
        logger.info("Shutting down ArxivMCPServerManager")

        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")

        try:
            # Use the exit stack to properly close all contexts
            # This will handle the session and client cleanup
            await self.exit_stack.aclose()
            
            # Reset all references
            self.session = None
            self.read_stream = None
            self.write_stream = None
            self.client = None
            
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")
        
        logger.info("ArxivMCPServerManager shutdown complete")