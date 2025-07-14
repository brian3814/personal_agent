import json
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Optional, List

from fastmcp.utilities.logging import get_logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from personal_agent.mcp.server.arxiv import ArxivMCPServerManager
from personal_agent.mcp.client.base import BaseMcpClient

logger = get_logger(__name__)

class ArxivMCPClient(BaseMcpClient):    
    def __init__(
        self, 
        *, 
        server_manager: Optional[ArxivMCPServerManager] = None,
        storage_path: Optional[str] = None
    ):
        self.storage_path = storage_path or os.path.expanduser("~/.arxiv-mcp-server/papers")

        if server_manager is None:
            self.server_manager = ArxivMCPServerManager(storage_path=self.storage_path)
        else:
            self.server_manager = server_manager

        self.session: ClientSession = None  
        self._initialized = False
        self._initializing = False

    async def __aenter__(self):
        await self._ensure_mcp_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def close(self):
        """Properly close the MCP client but not the shared server manager"""
        if self._initialized and self.session:
            try:
                # Close session but don't shutdown server manager
                await self.session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
        
        # Don't shutdown server_manager here if it's shared
        # Only shutdown if this client owns the server_manager
        
        self._initialized = False
        self.session = None

    async def call_tool(self, tool_name: str, params: dict) -> dict:
        await self._ensure_mcp_connection()
        
        try:
            logger.info(f"Calling '{tool_name}' tool with params: {params}")
            result = await self.session.call_tool(
                name=tool_name,
                arguments=params
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
                else:
                    return {"content": str(content)}
            return {"error": "No content returned"}
                
        except Exception as e:
            logger.warning(f"Tool call failed: {e}")
            raise e
    
    async def call_prompt(self, prompt_name: str, params: dict) -> dict:
        await self._ensure_mcp_connection()
        
        try:
            logger.info(f"Calling '{prompt_name}' prompt with params: {params}")
            result = await self.session.get_prompt(
                name=prompt_name,
                arguments=params
            )
                
            if result.messages and len(result.messages) > 0:
                message = result.messages[0]
                if hasattr(message, 'content') and message.content:
                    if hasattr(message.content, 'text'):
                        return {"analysis": message.content.text}
                    else:
                        return {"analysis": str(message.content)}
            return {"error": "No prompt response"}
        except Exception as e:
            logger.warning(f"Prompt call failed: {e}")
            raise e
    
    async def search_papers(
        self, 
        query: str, 
        max_results: int = 10,
        date_from: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> dict:
        params = {
            "query": query,
            "max_results": max_results
        }
        
        if date_from:
            params["date_from"] = date_from
        if categories:
            params["categories"] = categories
            
        return await self.call_tool("search_papers", params)
    
    async def download_paper(self, paper_id: str) -> dict:
        """Download a paper using persistent MCP client"""
        return await self.call_tool("download_paper", {"paper_id": paper_id})
    
    async def read_paper(self, paper_id: str) -> dict:
        """Read content of a downloaded paper"""
        return await self.call_tool("read_paper", {"paper_id": paper_id})
    
    async def list_papers(self) -> dict:
        """List all downloaded papers"""
        return await self.call_tool("list_papers", {})
    
    async def deep_analysis(self, paper_id: str) -> dict:
        """Perform deep analysis using the built-in prompt"""
        return await self.call_prompt("deep-paper-analysis", {"paper_id": paper_id})