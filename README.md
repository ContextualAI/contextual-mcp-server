# Contextual MCP Server

A Model Context Protocol (MCP) server that provides RAG (Retrieval-Augmented Generation) capabilities using Contextual AI. This server integrates with a variety of MCP clients. It provides flexibility in you can decide what functionality to offer in the server. In this readme, we will show integration with the both Cursor IDE and Claude Desktop.

Contextual AI now offers a hosted server inside the platform available at: https://mcp.app.contextual.ai/mcp/   
After you connect to the server, you can use the tools, such as query, provided by the platform MCP server.  
For a complete walkthrough, check out the MCP [user guide](https://docs.contextual.ai/user-guides/mcp-server).


## Overview

An MCP server acts as a bridge between AI interfaces (Cursor IDE or Claude Desktop) and a specialized Contextual AI agent. It enables:

1. **Query Processing**: Direct your domain specific questions to a dedicated Contextual AI agent
2. **Intelligent Retrieval**: Searches through comprehensive information in your knowledge base
3. **Context-Aware Responses**: Generates answers that are:
  - Grounded in source documentation
  - Include citations and attributions
  - Maintain conversation context


### Integration Flow

```
Cursor/Claude Desktop → MCP Server → Contextual AI RAG Agent
        ↑                  ↓             ↓                         
        └──────────────────┴─────────────┴─────────────── Response with citations
```

## Prerequisites

- Python 3.10 or higher
- Cursor IDE and/or Claude Desktop
- Contextual AI API key
- MCP-compatible environment


## Installation

1. Clone the repository:
```bash
git clone https://github.com/ContextualAI/contextual-mcp-server.git
cd contextual-mcp-server
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -e .
```

## Configuration

### Configure MCP Server

The server requires modifications of settings or use.
For example, the single_agent server should be customized with an appropriate docstring for your RAG Agent.

The docstring for your query tool is critical as it helps the MCP client understand when to route questions to your RAG agent. Make it specific to your knowledge domain. Here is an example:
```
A research tool focused on financial data on the largest US firms
```
or
```
A research tool focused on technical documents for Omaha semiconductors
```

The server also requires the following settings from your RAG Agent:
- `API_KEY`: Your Contextual AI API key
- `AGENT_ID`: Your Contextual AI agent ID

If you'd like to store these files in `.env` file you can specify them like so:

```bash
cat > .env << EOF
API_KEY=key...
AGENT_ID=...
EOF
```

The repo also contains more advance MPC servers for multi-agent systems or a [document-agent](https://www.linkedin.com/feed/update/urn:li:activity:7346595035770929152/).

### AI Interface Integration

This MCP server can be integrated with a variety of clients. To use with either Cursor IDE or Claude Desktop create or modify the MCP configuration file in the appropriate location:

1. First, find the path to your `uv` installation:
```bash
UV_PATH=$(which uv)
echo $UV_PATH
# Example output: /Users/username/miniconda3/bin/uv
```

2. Create the configuration file using the full path from step 1:

```bash
cat > mcp.json << EOF
{
 "mcpServers": {
   "ContextualAI-TechDocs": {
     "command": "$UV_PATH", # make sure this is set properly
     "args": [
       "--directory",
       "\${workspaceFolder}",  # Will be replaced with your project path
       "run",
       "multi-agent/server.py"
     ]
   }
 }
}
EOF
```

3. Move to the correct folder location, see below for options:

```bash
mkdir -p .cursor/
mv mcp.json .cursor/
```

Configuration locations:
- For Cursor:
 - Project-specific: `.cursor/mcp.json` in your project directory
 - Global: `~/.cursor/mcp.json` for system-wide access
- For Claude Desktop:
 - Use the same configuration file format in the appropriate Claude Desktop configuration directory


### Environment Setup

This project uses `uv` for dependency management, which provides faster and more reliable Python package installation.

## Usage

The server provides Contextual AI RAG capabilities using the python SDK, which can available a variety of commands accessible from MCP clients, such as Cursor IDE and Claude Desktop.
The current server focuses on using the query command from the Contextual AI python SDK, however you could extend this to support other features such as listing all the agents, updating retrieval settings, updating prompts, extracting retrievals, or downloading metrics.

### Example Usage
```python
# In Cursor, you might ask:
"Show me the code for initiating the RF345 microchip?"

# The MCP client will:
1. Determine if this should be routed to the MCP Server

# Then the MCP server will:
1. Route the query to the Contextual AI agent
2. Retrieve relevant documentation
3. Generate a response with specific citations
4. Return the formatted answer to Cursor
```


### Key Benefits
1. **Accurate Responses**: All answers are grounded in your documentation
2. **Source Attribution**: Every response includes references to source documents
3. **Context Awareness**: The system maintains conversation context for follow-up questions
4. **Real-time Updates**: Responses reflect the latest documentation in your datastore


## Development

### Modifying the Server

To add new capabilities:

1. Add new tools by creating additional functions decorated with `@mcp.tool()`
2. Define the tool's parameters using Python type hints
3. Provide a clear docstring describing the tool's functionality

Example:
```python
@mcp.tool()
def new_tool(param: str) -> str:
   """Description of what the tool does"""
   # Implementation
   return result
```

## Limitations

- The server runs locally and may not work in remote development environments
- Tool responses are subject to Contextual AI API limits and quotas
- Currently only supports stdio transport mode


For all the capabilities of Contextual AI, please check the [official documentation](https://docs.contextual.ai/).
