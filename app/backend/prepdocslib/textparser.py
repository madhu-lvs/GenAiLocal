"""
Text Parser Module

This module provides functionality for parsing plain text files into standardized Page objects.
It includes utilities for cleaning and normalizing text content while preserving meaningful formatting.

Key Components:
- TextParser: Main parser class for converting raw text content to Page objects
- cleanup_data: Utility function for standardizing text formatting

The module is designed to handle various text encodings and formats while producing
consistent output suitable for further processing.
"""

import logging
import re
from typing import IO, AsyncGenerator, Optional

from .page import Page
from .parser import Parser

logger = logging.getLogger(__name__)

def cleanup_data(data: str) -> str:
    """
    Cleans and normalizes text content using a series of formatting rules.
    
    Applies the following transformations:
    1. Replaces multiple consecutive newlines with a single newline
    2. Replaces multiple consecutive spaces with a single space (preserves newlines)
    3. Removes leading and trailing whitespace
    
    Args:
        data (str): Raw text content to be cleaned

    Returns:
        str: Cleaned and normalized text content
        
    Example:
        cleaned_text = cleanup_data("Hello   World\n\n\nTest")
        # Returns: "Hello World\nTest"
    """
    if not data:
        return ""
        
    try:
        # Replace multiple newlines with a single newline
        output = re.sub(r"\n{2,}", "\n", data)
        
        # Replace multiple spaces (not newlines) with a single space
        output = re.sub(r"[^\S\n]{2,}", " ", output)
        
        # Remove leading and trailing whitespace
        return output.strip()
        
    except Exception as e:
        logger.error(f"Error cleaning text data: {str(e)}")
        # Return original data if cleaning fails, ensuring the process continues
        return data.strip()


class TextParser(Parser):
    """
    Parser implementation for plain text content.
    
    Converts raw text content into Page objects while handling:
    - Text encoding
    - Content cleaning and normalization
    - Error recovery
    
    The parser processes the entire content as a single page, making it suitable
    for smaller text documents or when natural page breaks aren't required.
    
    Example:
        parser = TextParser()
        async for page in parser.parse(text_file):
            print(f"Page text: {page.text}")
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Parse text content into Page objects.
        
        Processes the input content stream and generates a single Page object
        containing the cleaned and normalized text.
        
        Args:
            content (IO): File-like object containing the text to parse
            
        Yields:
            Page: A page object containing the processed text content
            
        Raises:
            UnicodeDecodeError: If the content cannot be decoded as UTF-8
            IOError: If there are issues reading the content stream
            
        Note:
            - Always yields exactly one page for the entire content
            - Sets page number to 0 since text files are treated as single units
            - Handles UTF-8 encoded content by default
        """
        try:
            # Read and decode content
            data = content.read()
            if isinstance(data, bytes):
                decoded_data = data.decode("utf-8")
            else:
                decoded_data = str(data)
                
            # Clean and normalize the text
            cleaned_text = cleanup_data(decoded_data)
            
            if cleaned_text:
                logger.debug(f"Successfully parsed text content of length {len(cleaned_text)}")
                yield Page(
                    page_num=0,  # Single page format
                    offset=0,    # Start from beginning
                    text=cleaned_text
                )
            else:
                logger.warning("Parsed text content was empty after cleaning")
                
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode text content: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error parsing text content: {str(e)}")
            raise