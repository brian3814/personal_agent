import os
import asyncio
from textwrap import dedent
from typing import Any, AsyncIterable, Optional, List
from datetime import datetime, timedelta

from google.adk import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from personal_agent.mcp.client.arxiv import ArxivMCPClient
from personal_agent.mcp.server.arxiv import ArxivMCPServerManager

class ArxivResearchAgent:      
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(
        self, 
        *, 
        storage_path: str = './arxiv-mcp-server/papers'
    ):
        self.storage_path = storage_path
        self.mcp_server = ArxivMCPServerManager(storage_path=self.storage_path)
        """
        self.mcp_client = ArxivMCPClient(
            storage_path='./arxiv-mcp-server/papers',
            server_manager=self.mcp_server
        )
        """

        self.agent = None
        self.toolset = None
        self.exit_stack = None

    def start(self):
        self.toolset = self.mcp_server.get_toolset()
        self.agent = self._build_agent()

    def _build_agent(self) -> Agent:
        INSTRUCTION = dedent("""\
            You are an expert research assistant specializing in arXiv paper analysis. 
            You help users with:

            1. **Paper Search**: Find relevant papers using search_arxiv_papers() with:
            - Query terms for the research topic
            - Optional date filters for recent papers
            - Category filters (cs.AI, cs.LG, cs.CL, etc.)

            2. **Paper Analysis**: For individual papers:
            - Use download_arxiv_paper() to get the paper locally
            - Use read_arxiv_paper() to access content
            - Use analyze_paper_deeply() for comprehensive analysis

            3. **Research Workflows**: For broader research:
            - Use research_topic_workflow() for complete topic investigation
            - This automatically searches, downloads, and analyzes multiple papers

            4. **Paper Management**: 
            - Use list_downloaded_papers() to see what's available locally

            **Guidelines**:
            - Always download papers before trying to read or analyze them
            - For research topics, suggest using research_topic_workflow() for efficiency
            - Provide paper IDs, titles, and key findings in your responses
            - Recommend relevant arXiv categories when appropriate
            - For recent research, use date filters (format: YYYY-MM-DD)

            **arXiv categories**:
            You can find the list of categories here: https://arxiv.org/category_taxonomy
        """)
                    
        return Agent(
            model='gemini-2.0-flash-001',
            name='arxiv_research_agent',
            description=dedent("""\
                This agent helps researchers search, download, and analyze
                academic papers from arXiv. It can perform literature reviews,
                deep paper analysis, and research workflows.
            """),
            instruction=INSTRUCTION,
            tools=[
                self.toolset
            ]
        )
    
    async def cleanup(self):
        await self.mcp_server.shutdown()