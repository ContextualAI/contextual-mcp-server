from contextual import ContextualAI
from mcp.server.fastmcp import FastMCP
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Get API key and agent ID from environment variables
API_KEY = os.getenv("API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

# Create an MCP server
mcp = FastMCP("Contextual AI RAG Platform")

# Add query tool to interact with Contextual agent
@mcp.tool()
def query(prompt: str) -> str:
    """A RAG agent that can answer questions about data related to HSBC's market views"""
    client = ContextualAI(
        api_key=API_KEY,  # This is the default and can be omitted
    )
    query_result = client.agents.query.create(
        agent_id=AGENT_ID,
        messages=[{
            "content": prompt,
            "role": "user"
        }]
    )
    return query_result.message.content

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
