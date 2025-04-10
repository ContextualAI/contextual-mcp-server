from contextual import ContextualAI
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("CONTEXTUAL_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

# Create an MCP server
mcp = FastMCP("Contextual AI RAG Platform")

# Add query tool to interact with Contextual agent
@mcp.tool()
def query(prompt: str) -> str:
    """An enterprise search tool that can answer questions about a specific knowledge base"""
    client = ContextualAI(
        api_key=API_KEY,  # This is the default and can be omitted
    )
    query_result = client.agents.query.create(
        agent_id=AGENT,
        messages=[{
            "content": prompt,
            "role": "user"
        }]
    )
    return query_result.message.content

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
