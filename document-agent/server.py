import os
from typing import Annotated

from contextual import ContextualAI
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

load_dotenv()

API_KEY = os.getenv("API_KEY")
AGENT = os.getenv("AGENT")

# JOB_ID = "55bd4791-560a-46f7-b66f-fbe11bfa8b36"  # DeepSeek scaling report (14 pages)
# JOB_ID = "2e9c1615-c293-4475-b9d8-f9f6536bdf86"  # Qwen 3 tech report (35 pages)
JOB_ID = "794c58f2-38d4-454e-9a3e-05b8bab3dd5a"  # Bondcap AI report (340 pages)


class ParsedDocumentForAgent:
    """
    This class wraps `/parse` output exposing tool functions allowing an LLM agent to
    navigate and interact with the parsed document.

    0. read_document() -> str
    1. read_hierarchy() -> str, list[dict[id, level, markdown, page_index]]
    2. read_pages(page_indexes) -> str
    3. read_hierarchy_section(heading_block_id) -> str
    """

    def __init__(self, parsed_document):
        self.parsed_document = parsed_document
        self.block_map = {
            block.id: block
            for page in self.parsed_document.pages
            for block in page.blocks
        }
        self.heading_block_map = {
            block.id: block
            for block in self.parsed_document.document_metadata.hierarchy.blocks
        }

    def read_document(self) -> str:
        """
        Read contents of the entire document as markdown (may be large)
        """
        return self.parsed_document.markdown_document

    def read_hierarchy(self) -> tuple[str, list[dict]]:
        """
        Read the outline structure of the document as:
            (i) human/LLM readable markdown nested list
            (ii) LLM referenceable list of structured dicts

        Could provide either (ii) or both as context to an LLM to navigate the document and reference specific sections
        """
        hierarchy_markdown = (
            self.parsed_document.document_metadata.hierarchy.table_of_contents
        )

        hierarchy_list = []
        for block in self.parsed_document.document_metadata.hierarchy.blocks:
            hierarchy_list.append(
                {
                    "block_id": block.id,  # might need to translate the uuid to a LLM-friendly integer index instead
                    "hierarchy_level": block.hierarchy_level,
                    "markdown": block.markdown,
                    "page_index": block.page_index,
                }
            )
        return hierarchy_markdown, hierarchy_list

    def read_pages(self, page_indexes: list[int]) -> str:
        """
        Read the contents of the document for the provided page indexes
        """
        page_separator = "\n\n---\nPage index: {page_index}\n\n"
        content = ""
        for page_index in page_indexes:
            content += (
                page_separator.format(page_index=page_index)
                + self.parsed_document.pages[page_index].markdown
            )
        return content

    def read_hierarchy_section(self, heading_block_id: str) -> str:
        """
        Read the contents of the document that are children of the given heading block referenced by `heading_block_id`
        """
        heading_block = self.heading_block_map[heading_block_id]
        parent_path_prefix = heading_block.parent_ids + [heading_block_id]

        section_blocks = []
        for page in self.parsed_document.pages:
            for block in page.blocks:
                # filter for blocks that share the same parent path
                if block.parent_ids[: len(parent_path_prefix)] == parent_path_prefix:
                    section_blocks.append(block)

        section_content = "\n".join([block.markdown for block in section_blocks])
        section_prefix = "\n".join(
            [
                self.heading_block_map[block_id].markdown
                for block_id in parent_path_prefix
            ]
        )

        return section_prefix + "\n\n" + section_content


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


# Create an MCP server
navigable_document = initialize_navigable_document(JOB_ID)
document_title = navigable_document.parsed_document.document_metadata.hierarchy.blocks[
    0
].markdown
mcp = FastMCP(
    name=f"CTXL Document Agent for: {document_title}",
    instructions=f"""
    You are a document comprehension agent for the document titled: {document_title}.

    You can use the following tools to navigate the document:
        - read_document() -> str: Read contents of the entire document as markdown (may be large)
        - read_hierarchy() -> str: Read the outline structure of the document as a markdown list with nested headings and page indexes
        - read_pages(page_indexes: list[int]) -> str: Read the contents of the document for the provided page indexes

    Guidance:
        - If asked for summaries or outlines of the document use both the hierarchy and read sections from the first few pages of the document for context.
        - You can use the `read_pages()` tool to navigate to specific sections of the document by their corresponding page indexes in the document hierarchy.
    """,
)


# Expose MCP tools for each method in the navigable document
@mcp.tool()
def read_document() -> str:
    """Read contents of the entire document as markdown (may be large)"""
    return navigable_document.read_document()


@mcp.tool()
def read_hierarchy() -> str:
    """Read a markdown nested list of the hierarchical structure of the document.

    This contains headings with their nesting as well as the page index where the section with this heading starts.
    The page indexes can be used to read the contents of the document for a specific section.
    """
    return navigable_document.read_hierarchy()[
        0
    ]  # only return the markdown string for now


@mcp.tool()
def read_pages(page_indexes: list[int]) -> str:
    """Read the contents of the document for the provided page indexes"""
    return navigable_document.read_pages(page_indexes)


# @mcp.tool()
# def read_hierarchy_section(heading_block_id: str) -> str:
#     """Read the contents of the document that are children of the given heading block referenced by `heading_block_id`"""
#     return navigable_document.read_hierarchy_section(heading_block_id)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
