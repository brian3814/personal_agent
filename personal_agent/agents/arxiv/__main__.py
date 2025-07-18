import os
import logging

import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from .arxiv import ArxivResearchAgent
from .arxiv_executor import ArxivResearchAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass

def main(host='localhost', port=10002):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        skill = AgentSkill(
            id='arxiv_research',
            name='Arxiv Research Tool',
            description='Helps with the latest arxiv papers searching and analyzing',
            tags=['arxiv'],
            examples=[
                'Can you research the latest papers related to the topic of 3D gaussain splatting?'
            ],
        )
        agent_card = AgentCard(
            name='Arxiv Research Agent',
            description='This agent handles the arxiv research process for the users given the topic of the research.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=ArxivResearchAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ArxivResearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
        )
        request_handler = DefaultRequestHandler(
            agent_executor=ArxivResearchAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port, timeout_keep_alive=None)
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()