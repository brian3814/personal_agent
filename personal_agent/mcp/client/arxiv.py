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

logger = get_logger(__name__)

class ArxivMCPClient:    
    def __init__(
        self, 
        *, 
        storage_path: Optional[str] = None, 
        server_manager: Optional[ArxivMCPServerManager] = None
    ):
        self.storage_path = storage_path or os.path.expanduser("~/.arxiv-mcp-server/papers")
        self._session = None
        self.server_manager = server_manager or ArxivMCPServerManager(storage_path)
    
    def shutdown(self):
        self.server_manager.shutdown()
    
    @asynccontextmanager
    async def get_session(self):
        """Get an active MCP session to the ArXiv server"""
        
        if self._session is not None:
            yield self._session
            return
        
        async with self.server_manager.stdio_client as (read_stream, write_stream):
            async with ClientSession(read_stream=read_stream, write_stream=write_stream) as session:
                await session.initialize()
                yield session
    
    async def call_tool(self, tool_name: str, params: dict) -> dict:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    logger.info(f"Calling '{tool_name}' tool with params: {params}")
                    result = await session.call_tool(
                        name=tool_name,
                        arguments=params
                    )
                    
                    # Parse the response
                    if result.content and len(result.content) > 0:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            return json.loads(content.text)
                        else:
                            return {"content": str(content)}
                    return {"error": "No content returned"}
                    
            except Exception as e:
                logger.warning(f"Tool call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise
    
    async def call_prompt(self, prompt_name: str, params: dict) -> dict:
        """Call a prompt on the ArXiv MCP server"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    logger.info(f"Calling '{prompt_name}' prompt with params: {params}")
                    result = await session.get_prompt(
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
                logger.warning(f"Prompt call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise
    
    async def search_papers(
        self, 
        query: str, 
        max_results: int = 10,
        date_from: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> dict:
        """Search for papers on arXiv"""
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
        """Download a specific paper by ID"""
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
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.shutdown()

async def search_papers_async(
    client: ArxivMCPClient,
    query: str, 
    max_results: int = 10,
    date_from: Optional[str] = None,
    categories: Optional[List[str]] = None
) -> dict:
    """Async wrapper for paper search"""
    return await client.search_papers(query, max_results, date_from, categories)

async def download_paper_async(client: ArxivMCPClient, paper_id: str) -> dict:
    """Async wrapper for paper download"""
    return await client.download_paper(paper_id)

async def read_paper_async(client: ArxivMCPClient, paper_id: str) -> dict:
    """Async wrapper for reading paper"""
    return await client.read_paper(paper_id)

async def list_papers_async(client: ArxivMCPClient) -> dict:
    """Async wrapper for listing papers"""
    return await client.list_papers()

async def analyze_paper_async(client: ArxivMCPClient, paper_id: str) -> dict:
    """Async wrapper for deep paper analysis"""
    return await client.deep_analysis(paper_id)