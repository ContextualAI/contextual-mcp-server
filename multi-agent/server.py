from contextual import ContextualAI
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("CONTEXTUAL_API_KEY")

# Create an MCP server
mcp = FastMCP("Contextual AI RAG Platform")

# Add query tool to interact with Contextual agent
@mcp.tool()
def query(prompt: str) -> str:
    """An enterprise search tool that can answer questions about any sort of knowledge base"""

    client = ContextualAI(
        api_key=API_KEY,  # This is the default and can be omitted
    )

    instruction = "Rank documents based on their ability to answer the question/query"

    agents = {}
    for agent in client.agents.list():
        agents.update({agent.id: f"{agent.name} - {agent.description}"})
    documents = list(agents.values())

    results = client.rerank.create(
        model="ctxl-rerank-en-v1-instruct",
        instruction=instruction,
        query=prompt,
        documents=documents,
        metadata=metadata,
        top_n=1
    )

    agent_index = results.results[0].index
    agent_id = list(agents.keys())[agent_index]

    query_result = client.agents.query.create(
        agent_id=agent_id,
        messages=[{
            "content": prompt,
            "role": "user"
        }]
    )
    return query_result.message.content

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
