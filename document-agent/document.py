class ParsedDocumentNavigator:
    """
    This class wraps `/parse` API output exposing methods enabling an LLM agent to
    navigate and interact with the parsed document.
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
        return self.read_pages(list(range(len(self.parsed_document.pages))))

    def read_hierarchy(self) -> tuple[str, list[dict]]:
        """
        Read the parsed heading structure of the entire document.

        Result is a tuple of:
            (i) human/LLM readable document hierarchy with pages indexes (a.k.a. table of contents)
            (ii) JSON list of headings in the document hierarchy
        """
        hierarchy_markdown = (
            self.parsed_document.document_metadata.hierarchy.table_of_contents
        )

        hierarchy_list = []
        for block in self.parsed_document.document_metadata.hierarchy.blocks:
            hierarchy_list.append(
                {
                    "block_id": block.id,  # might need to translate uuid to a LLM-friendly integer index instead
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

    def read_heading_contents(self, heading_block_id: str) -> str:
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
