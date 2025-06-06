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
