class Page:
    """
    Represents a single page or section extracted from a document.
    
    This class serves as a fundamental data structure in the document processing pipeline,
    maintaining both the content and positional metadata for document sections. It enables
    accurate tracking of content location within larger documents, which is essential for:
    - Preserving document structure
    - Enabling accurate content referencing 
    - Supporting pagination features
    - Facilitating content reconstruction

    Attributes:
        page_num (int): Page number within the document (zero-based)
        offset (int): Character offset position in the full document text
        text (str): Actual content of the page
        
    Example:
        If a document contains two pages:
        - Page 1 text: "hello"
        - Page 2 text: "world"
        
        Then Page 2 would have:
        - page_num = 1
        - offset = 5 (length of "hello")
        - text = "world"
    """

    def __init__(self, page_num: int, offset: int, text: str):
        """
        Initialize a Page instance.

        Args:
            page_num: Zero-based page number in the document
            offset: Starting character position if entire document was concatenated
            text: Content of the page
        """
        self.page_num = page_num
        self.offset = offset
        self.text = text


class SplitPage:
    """
    Represents a section of a page that has been divided into smaller chunks.
    
    This class handles scenarios where pages need to be broken down into smaller,
    more manageable sections while maintaining page number references. This is
    particularly useful for:
    - Large page processing
    - Text chunking for embedding generation
    - Managing content size limits
    - Optimizing for specific model token limits

    Attributes:
        page_num (int): Original page number from source document
        text (str): Content of this specific section
    """

    def __init__(self, page_num: int, text: str):
        """
        Initialize a SplitPage instance.

        Args:
            page_num: Page number from the original document
            text: Content of this page section
        """
        self.page_num = page_num
        self.text = text