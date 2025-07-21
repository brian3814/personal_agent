# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal agent system built with FastAPI and Google's Agent Development Kit (ADK). The system provides conversational AI capabilities through a REST API, featuring specialized agents for research tasks, particularly arXiv paper analysis. It uses MCP (Model Context Protocol) servers to extend agent capabilities.

## Architecture

### Backend (Python)
- **FastAPI Server** (`personal_agent/main.py`): REST API with streaming responses and CORS support
- **Agent System**: Built on Google ADK with hierarchical agent structure
  - Root agent coordinates sub-agents
  - ArxivResearchAgent specializes in academic paper research
- **MCP Integration**: Model Context Protocol for extending agent capabilities
  - `personal_agent/mcp/server/` - MCP server implementations
  - `personal_agent/mcp/client/` - MCP client wrappers
- **Session Management**: In-memory session handling with 3-hour timeout
- **Base Classes**: `personal_agent/agents/base.py` provides common agent interface

### Frontend (React)
- **Simple UI** (`ui/simple/`): React + Vite chat interface
- **State Management**: Zustand for chat state
- **Components**: Modular chat UI with message bubbles, input, and headers
- **Real-time**: Server-Sent Events for streaming responses

## Development Commands

### Backend (Python)
```bash
# Start the server (requires GOOGLE_API_KEY environment variable)
python -m personal_agent

# With custom model and port
python -m personal_agent --model gemini-2.0-flash-001 --host 0.0.0.0 --port 5050
```

### Frontend (React)
```bash
cd ui/simple
npm install
npm run dev      # Development server
npm run build    # Production build
npm run lint     # ESLint
npm run preview  # Preview production build
```

## Environment Setup

1. Set Google API key:
   ```bash
   export GOOGLE_API_KEY={your_api_key}
   ```

2. Install Python dependencies via uv (pyproject.toml defines dependencies)

3. The server runs on port 5050 by default, frontend dev server on 5173

## Key Implementation Details

- **Streaming Responses**: FastAPI returns Server-Sent Events for real-time chat
- **CORS Configuration**: Allows localhost:5173 for development
- **Agent Tools**: ArxivResearchAgent uses MCP toolsets for paper search, download, and analysis
- **Error Handling**: Custom response processing with JSON serialization for tool results
- **Session Persistence**: In-memory session service with automatic cleanup

## Common Patterns

- Agents inherit from BaseAgent and implement cleanup() method
- MCP clients extend BaseMcpClient for connection management
- FastAPI routes use streaming responses for chat interactions
- React components follow modern patterns with hooks and functional components