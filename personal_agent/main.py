import os
import time
import json
import argparse
import signal
from textwrap import dedent

from fastapi import FastAPI, Request
from fastapi_mcp import FastApiMCP
from fastapi.responses import StreamingResponse
from google.genai.types import Content, Part
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from contextlib import asynccontextmanager

from personal_agent.agents import ArxivResearchAgent
from personal_agent.query import Query

DEFAULT_USER_ID = "user_id"

app = FastAPI()
mcp = FastApiMCP(app, name="personalAgent", description="Personal Agent")
mcp.mount()

session_manager = None
runner = None
sub_agents = []

def create_root_agent(
    *,
    model="gemini-2.0-flash-001",
    sub_agents=None
):
    if sub_agents is None:
        sub_agents = []

    return Agent(
        name="root_agent",
        model=model,
        description="The root agent of the personal agent",
        instruction=dedent("""\
            You are the root agent of the personal agent.
            You are responsible for coordinating the other agents.
        """),
        sub_agents=sub_agents
    )

class SessionManager:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.session_timeout = 3 * 60 * 60  # 3 hours
        self.user_sessions = {}
        self.sessions = {}
        self.session_last_active = {}
    
    def update_session_activity(self, user_id: str):
        self.session_last_active[user_id] = time.time()
    
    def clear_expired_sessions(self):
        current_time = time.time()
        expired_users = []
        
        for user_id, last_active in self.session_last_active.items():
            if current_time - last_active > self.session_timeout:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            session_id = self.user_sessions.pop(user_id, None)
            if session_id:
                self.sessions.pop(session_id, None)
                self.session_last_active.pop(user_id, None)
    
    def check_session(self, user_id: str):
        return user_id in self.user_sessions
    
    async def get_session_id(self, user_id: str):
        if not self.check_session(user_id):
            session_id = f'session_{user_id}'
            self.user_sessions[user_id] = session_id
            
            # Create session in session service
            await self.session_service.create_session(
                app_name="personal_agent",
                user_id=user_id,
                session_id=session_id
            )
            
            # Track session metadata
            self.sessions[session_id] = {
                'user_id': user_id,
                'last_activity': time.time(),
                'session_data': {}
            }
        else:
            session_id = self.user_sessions[user_id]
        
        self.update_session_activity(user_id)
        self.clear_expired_sessions()
        
        return session_id

def create_runner(agent):
    return Runner(
        app_name="personal_agent",
        agent=agent,
        session_service=session_manager.session_service,
    )

async def process_response(response_generator):
    async for event in response_generator:
        if hasattr(event, 'content'):
            data = json.dumps({
                'role': 'assistant',
                'content': str(event.content)
            }, ensure_ascii=False)

            yield f'event: message\ndata: {data}\n\n'

@asynccontextmanager
async def lifespan(app):
    arxiv_agent = ArxivResearchAgent()
    app.state.arxiv_agent = arxiv_agent
    yield
    await arxiv_agent.cleanup()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def greeting():
    return {"message": "Hello, I'm your personal assistant!"}

@app.get("/query")
async def query(q: str, request: Request):
    user_id = request.cookies.get("user_id", DEFAULT_USER_ID)
    session_id = await session_manager.get_session_id(user_id)

    content = Content(role="user", parts=[Part(text=q)])
    response = runner.run_async(
        new_message=content,
        user_id=user_id,
        session_id=session_id,
    )

    return StreamingResponse(
        process_response(response), 
        media_type="text/event-stream"
    )

@app.post("/query")
async def query(query: Query, request: Request):
    user_id = request.cookies.get("user_id", DEFAULT_USER_ID)
    session_id = await session_manager.get_session_id(user_id)

    content = Content(role="user", parts=[Part(text=query.query)])
    response = runner.run_async(
        new_message=content,
        user_id=user_id,
        session_id=session_id,
    )

    return StreamingResponse(
        process_response(response), 
        media_type="text/event-stream"
    )

def handle_signal(signum, frame):
    print(f"Received signal {signum}, cleaning up...")
    for agent in sub_agents:
        if hasattr(agent, 'cleanup'):
            agent.cleanup()
    exit(0)

def get_sub_agents():
    arxiv_agent = ArxivResearchAgent()
    arxiv_agent.start()

    return [
        arxiv_agent.agent
    ]

def main():
    global session_manager, runner, sub_agents
    
    parser = argparse.ArgumentParser(description="Personal Agent Server")
    parser.add_argument("--model", default="gemini-2.0-flash-001", 
                       help="LLM model to use (default: gemini-2.0-flash-001)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5050, help="Port to bind to")
    
    args = parser.parse_args()
    
    session_manager = SessionManager()
    sub_agents = get_sub_agents()
    root_agent = create_root_agent(model=args.model, sub_agents=sub_agents)
    runner = create_runner(root_agent)
    
    print(f"Starting Personal Agent with model: {args.model}")
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    start_server(args.host, args.port)

def start_server(host, port):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()