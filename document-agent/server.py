import os
from typing import Annotated

from contextual import ContextualAI
from document import ParsedDocumentForAgent
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from tiktoken import encoding_for_model

load_dotenv()

API_KEY = os.getenv("API_KEY")
AGENT = os.getenv("AGENT")

JOB_ID_DEEPSEEK = (
    "55bd4791-560a-46f7-b66f-fbe11bfa8b36"  # DeepSeek scaling report (14 pages)
)
JOB_ID_QWEN = "2e9c1615-c293-4475-b9d8-f9f6536bdf86"  # Qwen 3 tech report (35 pages)
JOB_ID_BONDCAP = "794c58f2-38d4-454e-9a3e-05b8bab3dd5a"  # Bondcap AI report (340 pages)
JOB_ID_USGOV_FIN_24 = (
    "0817e279-3c45-49fe-b6f0-76010d0e5205"  # US Gov Financial report 2024 (247 pages)
)


def initialize_navigable_document(job_id: str):
    # Create CTX client
    ctxl_client = ContextualAI(api_key=API_KEY)
    # Fetch document
    parsed_document = ctxl_client.parse.job_results(
        job_id, output_types=["markdown-per-page", "blocks-per-page"]
    )
    # Make agent navigable document
    navigable_document = ParsedDocumentForAgent(parsed_document)
    return navigable_document


def count_tokens_fast(text: str) -> int:
    """
    Count tokens in a string using a fast approximation.
    """
    multiplier = 1.0
    max_chars = 80000  # ~20k tokens
    if len(text) > max_chars:
        multiplier = len(text) / max_chars
        text = text[:max_chars]
    encoding = encoding_for_model("gpt-4o")
    n_tokens = len(encoding.encode(text))
    return int(n_tokens * multiplier)


# Create an MCP server
navigable_document = initialize_navigable_document(JOB_ID_BONDCAP)
document_title = navigable_document.parsed_document.document_metadata.hierarchy.blocks[
    0
].markdown
mcp = FastMCP(
    name=f"CTXL Document Agent for: {document_title}",
    instructions=f"""
    You are a document comprehension agent for the document titled: {document_title}.
    """,
)


@mcp.tool()
def initialize_document_agent(job_id: str) -> str:
    """
    Initialize the document agent with a provided job id.

    Guidance:
        - When asked for an outline of the document, read the hierarchy and then look up an initial first few pages of the document before answering.
        - Use this to request the user to provide a job id for a document so you can answer questions about it.
    """
    global navigable_document
    navigable_document = initialize_navigable_document(job_id)
    message = f"Document agent initialized for job id: {job_id}"
    # add summary stats for the document
    n_pages = len(navigable_document.parsed_document.pages)
    n_doc_tokens = count_tokens_fast(navigable_document.read_document())
    n_hierarchy_tokens = count_tokens_fast(navigable_document.read_hierarchy()[0])
    stats = f"""
        - document has {n_doc_tokens} tokens, {n_pages} pages 
        - hierarchy has {n_hierarchy_tokens} tokens
    """
    return f"{message}\n{stats}"


@mcp.tool()
def read_hierarchy() -> str:
    """
    Read a markdown nested list of the hierarchical structure of the document.
    This contains headings with their nesting as well as the page index where the section with this heading starts.

    Guidance:
        - Use these results to look up the start and end page indexes to read the contents of a specific section for further context.
    """
    return navigable_document.read_hierarchy()[
        0
    ]  # only return the markdown string for now


@mcp.tool()
def read_pages(rationale: str, start_index: int, end_index: int) -> str:
    """
    Read the contents of the document between the start and end page indexes, inclusive.
    Provide a very brief rationale for what you are trying to read e.g. the name of the section or other context.
    """
    page_indexes = list(range(start_index, end_index + 1))
    return navigable_document.read_pages(page_indexes)


# # Expose MCP tools for each method in the navigable document
# @mcp.tool()
# def read_document() -> str:
#     """
#     Read contents of the entire document as markdown (may be large)
#     """
#     return navigable_document.read_document()

# @mcp.tool()
# def read_hierarchy_section(heading_block_id: str) -> str:
#     """Read the contents of the document that are children of the given heading block referenced by `heading_block_id`"""
#     return navigable_document.read_hierarchy_section(heading_block_id)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
