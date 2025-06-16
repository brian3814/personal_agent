import asyncio
from typing import Any, AsyncIterable, Optional, List
from datetime import datetime, timedelta

from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from personal_agent.mcp.client.arxiv import ArxivMCPClient
from personal_agent.mcp.server.arxiv import create_server_manager, ArxivMCPServerManager

class ArxivResearchAgent:      
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    
    def __init__(
        self, 
        *, 
        llm_agent: LlmAgent = None, 
        user_id: str = 'arxiv_researcher',
        mcp_server_manager: Optional[ArxivMCPServerManager] = None
    ):
        self._agent = llm_agent if llm_agent is not None else self._build_llm_agent()
        self._user_id = user_id
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        self.mcp_server_manager = mcp_server_manager or create_server_manager(storage_path='./arxiv-mcp-server/papers')
        self.mcp_client = ArxivMCPClient(
            storage_path='./arxiv-mcp-server/papers',
            server_manager=self.mcp_server_manager
        )

    def _build_llm_agent(self) -> LlmAgent:
        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='arxiv_research_agent',
            description=(
                'This agent helps researchers search, download, and analyze '
                'academic papers from arXiv. It can perform literature reviews, '
                'deep paper analysis, and research workflows.'
            ),
            instruction="""
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

**Common arXiv categories**:
- cs.AI: Artificial Intelligence
- cs.LG: Machine Learning  
- cs.CL: Computation and Language
- cs.CV: Computer Vision
- cs.RO: Robotics
- stat.ML: Machine Learning (Statistics)
            """,
            tools=[
                self.search_arxiv_papers,
                self.download_arxiv_paper,
                self.read_arxiv_paper,
                self.list_downloaded_papers,
                self.analyze_paper_deeply,
                self.research_topic_workflow,
            ],
        )
    
    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        
        content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=query)]
        )
        
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            if event.is_final_response():
                response = ''
                if (
                    event.content 
                    and event.content.parts 
                    and event.content.parts[0].text
                ):
                    response = '\n'.join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (
                    event.content 
                    and event.content.parts 
                    and any([
                        True for p in event.content.parts 
                        if p.function_response
                    ])
                ):
                    response = next(
                        p.function_response.model_dump() 
                        for p in event.content.parts
                    )
                
                yield {
                    'is_task_complete': True,
                    'content': response,
                }
            else:
                yield {
                    'is_task_complete': False,
                    'updates': 'Searching and analyzing arXiv papers...',
                }

    async def search_arxiv_papers(
        self,
        query: str,
        max_results: Optional[int] = 10,
        date_from: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> dict[str, Any]:
        """
        Search for papers on arXiv with optional filters.
        
        Args:
            query (str): Search query for papers
            max_results (int): Maximum number of results to return
            date_from (str): Filter papers from this date (YYYY-MM-DD format)
            categories (List[str]): arXiv categories to filter by (e.g., ["cs.AI", "cs.LG"])
        
        Returns:
            dict[str, Any]: Search results containing paper information
        """
        params = {
            "query": query,
            "max_results": max_results or 10
        }
        
        if date_from:
            params["date_from"] = date_from
        if categories:
            params["categories"] = categories
        
        result = await self.mcp_client.call_tool("search_papers", params)
        return result

    async def download_arxiv_paper(
        self,
        paper_id: str
    ) -> dict[str, Any]:
        """
        Download a specific paper by its arXiv ID.
        
        Args:
            paper_id (str): The arXiv paper ID (e.g., "2401.12345")
        
        Returns:
            dict[str, Any]: Download result with success status
        """
        result = await self.mcp_client.call_tool("download_paper", {"paper_id": paper_id})
        return result

    async def read_arxiv_paper(
        self,
        paper_id: str
    ) -> dict[str, Any]:
        """
        Read the content of a downloaded paper.
        
        Args:
            paper_id (str): The arXiv paper ID to read
        
        Returns:
            dict[str, Any]: Paper content and metadata
        """
        result = await self.mcp_client.call_tool("read_paper", {"paper_id": paper_id})
        return result

    async def list_downloaded_papers(self) -> dict[str, Any]:
        """
        List all papers that have been downloaded locally.
        
        Returns:
            dict[str, Any]: List of downloaded papers with metadata
        """
        result = await self.mcp_client.call_tool("list_papers", {})
        return result

    async def analyze_paper_deeply(
        self,
        paper_id: str
    ) -> dict[str, Any]:
        """
        Perform comprehensive analysis of a paper using built-in research prompts.
        
        Args:
            paper_id (str): The arXiv paper ID to analyze
        
        Returns:
            dict[str, Any]: Detailed analysis including summary, methodology, implications
        """
        result = await self.mcp_client.call_prompt("deep-paper-analysis", {"paper_id": paper_id})
        return result

    async def research_topic_workflow(
        self,
        topic: str,
        num_papers: Optional[int] = 5,
        recent_only: Optional[bool] = True,
        categories: Optional[List[str]] = None,
    ) -> dict[str, Any]:
        """
        Complete research workflow: search -> download -> analyze papers on a topic.
        
        Args:
            topic (str): Research topic to investigate
            num_papers (int): Number of papers to analyze
            recent_only (bool): Whether to focus on recent papers (last year)
            categories (List[str]): arXiv categories to search in
        
        Returns:
            dict[str, Any]: Comprehensive research summary with analyses
        """
        # Set date filter for recent papers
        date_from = None
        if recent_only:
            date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Search for papers
        search_results = await self.search_arxiv_papers(
            query=topic,
            max_results=num_papers or 5,
            date_from=date_from,
            categories=categories
        )
        
        if not search_results.get("papers"):
            return {"error": "No papers found for the topic", "topic": topic}
        
        # Download and analyze papers
        analyses = []
        for paper in search_results["papers"][:num_papers or 5]:
            paper_id = paper["id"]
            
            # Download paper
            download_result = await self.download_arxiv_paper(paper_id)
            if not download_result.get("success"):
                continue
            
            # Perform analysis
            analysis = await self.analyze_paper_deeply(paper_id)
            analyses.append({
                "paper_id": paper_id,
                "title": paper.get("title"),
                "authors": paper.get("authors"),
                "analysis": analysis
            })
        
        return {
            "topic": topic,
            "total_papers_found": len(search_results["papers"]),
            "analyzed_papers": len(analyses),
            "analyses": analyses,
            "summary": f"Analyzed {len(analyses)} papers on '{topic}'"
        }
