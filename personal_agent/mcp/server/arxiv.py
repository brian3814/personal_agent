import os
import subprocess
import threading
import atexit
from typing import Optional

from fastmcp.utilities.logging import get_logger
from mcp import StdioServerParameters
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
        self.stdio_client = None
        self.start_server()
    
    def start_server(self):
        try:
            stdio_params = StdioServerParameters(
                command='uv',
                args=[
                    'tool',
                    'run',
                    'arxiv-mcp-server',
                    '--storage-path', self.storage_path
                ],
                env=os.environ.copy()
            )

            self.stdio_client = stdio_client(stdio_params)
                    
        except Exception as e:
            logger.error(f"Failed to start ArXiv MCP server: {e}")
            raise
            
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.shutdown()

def create_server_manager(
    *, 
    storage_path: Optional[str] = None, 
    host: str = 'localhost',
    port: int = 10002
) -> ArxivMCPServerManager:
    return ArxivMCPServerManager(storage_path=storage_path)