import logging
import re
from typing import IO, AsyncGenerator

from bs4 import BeautifulSoup

from .page import Page
from .parser import Parser

logger = logging.getLogger("scripts")


def cleanup_data(data: str) -> str:
    """
    Cleans up extracted HTML text content by normalizing whitespace and formatting.
    
    Performs three primary cleanup operations:
    1. Replaces multiple newlines with a single newline
    2. Normalizes multiple spaces while preserving intentional line breaks
    3. Standardizes multiple hyphens to double-hyphens
    
    Args:
        data (str): Raw text content extracted from HTML
        
    Returns:
        str: Cleaned and normalized text content
        
    Example:
        cleanup_data("Hello   World\n\n\nTest")
        "Hello World\nTest"
    """
    # Replace multiple newlines with a single newline
    output = re.sub(r"\n{2,}", "\n", data)
    
    # Replace multiple spaces (excluding newlines) with a single space
    output = re.sub(r"[^\S\n]{2,}", " ", output)
    
    # Standardize multiple hyphens to double-hyphens
    output = re.sub(r"-{2,}", "--", output)

    return output.strip()


class LocalHTMLParser(Parser):
    """
    Parses HTML content into Page objects using BeautifulSoup4.
    
    This parser extracts clean, readable text from HTML documents while:
    - Removing all HTML tags and formatting
    - Preserving text content and structure
    - Normalizing whitespace and formatting
    - Handling HTML entities correctly
    
    The parser processes HTML files sequentially, treating the entire content
    as a single page. Multi-page HTML documents are not currently supported.
    
    Implementation:
    - Uses BeautifulSoup4 with the 'html.parser' backend for maximum compatibility
    - Applies text cleanup and normalization after extraction
    - Maintains consistent page numbering (always 0 for single-page documents)
    
    Note:
        This parser is intended for local HTML files. For web-based HTML content,
        additional handling may be required for encoding and remote resources.
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Parses an HTML file and extracts its text content into a Page object.
        
        Args:
            content (IO): A file-like object containing the HTML content to parse
            
        Yields:
            Page: A single Page object containing the extracted and cleaned text
                 with page number 0 and starting offset 0
                 
        Example:
            parser = LocalHTMLParser()
            async for page in parser.parse(open('document.html', 'rb')):
            ...     print(page.text)
            
        Note:
            The parser currently treats all HTML content as a single page. If you need
            to split the content into multiple pages, consider using a TextSplitter
            after parsing.
        """
        logger.info("Extracting text from '%s' using local HTML parser (BeautifulSoup)", content.name)

        # Read and parse HTML content
        data = content.read()
        soup = BeautifulSoup(data, "html.parser")

        # Extract text content, removing all HTML tags
        result = soup.get_text()

        # Yield a single page with cleaned text
        yield Page(0, 0, text=cleanup_data(result))