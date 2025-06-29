import os
from contextlib import AsyncExitStack
from typing import Optional

from fastmcp.utilities.logging import get_logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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

    async def get_session(self):
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
        print("Shutting down ArxivMCPServerManager")

        if self.session:
            await self.session.close()
        if self.client:
            await self.client.__aexit__(None, None, None)

        print("ArxivMCPServerManager shutdown complete")