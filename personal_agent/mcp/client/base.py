import os
import json
import asyncio
import time
import requests
from pydantic import BaseModel

from fastapi import Request, HTTPException, APIRouter
from google.adk import Agent, Runner
from google.adk.tools import google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google.adk.sessions import InMemorySessionService


class BaseMcpClient:
    def __init__(self):
        self.server_manager = None
        self.session = None  
        self._initialized = False
        self._initializing = False

    async def _ensure_mcp_connection(self):
        if self._initialized:
            return
        
        if self._initializing:
            while not self._initialized:
                await asyncio.sleep(0.1)
            return

        self._initializing = True
        
        if self.session is None:
            await self.server_manager.get_session()
            self.session = self.server_manager.session
            
        self._initialized = True
        self._initializing = False