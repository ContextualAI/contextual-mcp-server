import os

from contextual import ContextualAI
from document import ParsedDocumentNavigator
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tiktoken import encoding_for_model

load_dotenv()

API_KEY = os.getenv("API_KEY")


def initialize_document_navigator(parse_job_id: str):
    ctxl_client = ContextualAI(api_key=API_KEY)
    parsed_document = ctxl_client.parse.job_results(
        parse_job_id, output_types=["markdown-per-page", "blocks-per-page"]
    )
    document_navigator = ParsedDocumentNavigator(parsed_document)
    return document_navigator


def count_tokens_fast(text: str) -> int:
    """
    Count tokens in a string using a fast approximation.
    """
    multiplier, max_chars = 1.0, 80000  # ~20k tokens
    if len(text) > max_chars:
        multiplier = len(text) / max_chars
        text = text[:max_chars]
    n_tokens = len(encoding_for_model("gpt-4o").encode(text))
    return int(n_tokens * multiplier)


document_navigator = None
mcp = FastMCP(
    name="CTXL Document Agent",
    instructions="""
    You are a document comprehension agent that can read, summarize and navigate a document.
    """,
)


@mcp.tool()
def initialize_document_agent(job_id: str) -> str:
    """
    Initialize the document agent with a provided job id.

    Guidance:
        - When asked for an outline of the document, read the hierarchy and then look up an initial few pages of the document before answering.
        - Use this to request the user to provide a job id for a document so you can answer questions about it.
    """
    global document_navigator
    document_navigator = initialize_document_navigator(job_id)
    message = f"Document agent initialized for job id: {job_id}"
    # add summary stats for the document
    n_pages = len(document_navigator.parsed_document.pages)
    n_doc_tokens = count_tokens_fast(document_navigator.read_document())
    n_hierarchy_tokens = count_tokens_fast(document_navigator.read_hierarchy()[0])
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
    return document_navigator.read_hierarchy()[
        0
    ]  # human/llm readable index structure for the document


@mcp.tool()
def read_pages(rationale: str, start_index: int, end_index: int) -> str:
    """
    Read the contents of the document between the start and end page indexes, both inclusive.
    Provide a brief 1-line rationale for what you are trying to read e.g. the name of the section or other context.
    """
    page_indexes = list(range(start_index, end_index + 1))
    return document_navigator.read_pages(page_indexes)


# NOTE: not used, but could be exposed with some control over context utilization
# @mcp.tool()
# def read_document() -> str:
#     """
#     Read contents of the entire document as markdown (may be large)
#     """
#     return document_navigator.read_document()

# NOTE: not used, as reading by page indexes was more flexible and reliable than getting LLM to reference headings by ID
# @mcp.tool()
# def read_heading_contents(heading_block_id: str) -> str:
#     """Read the contents of the document that are children of the given heading block referenced by `heading_block_id`"""
#     return document_navigator.read_heading_contents(heading_block_id)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
