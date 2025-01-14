"""
CSV Parser Module

This module provides functionality for parsing CSV files into Page objects for search indexing.
It handles both text and binary CSV file inputs, automatically detecting and decoding content
as needed. Each row of the CSV becomes a separate Page object with its own offset tracking.

Key Features:
- Automatic content type detection and decoding
- Skips header row by default
- Maintains consistent offset tracking for content positioning
- Handles both buffered and raw file inputs
"""

import csv
from typing import IO, AsyncGenerator, Union

from .page import Page
from .parser import Parser


class CsvParser(Parser):
    """
    Parses CSV files into individual Page objects, with each row becoming a separate page.
    
    This parser automatically handles different input types (bytes, string, BufferedReader)
    and properly decodes content while maintaining exact offsets for search indexing.
    Each row is treated as a distinct page, allowing for granular search results.
    
    The parser skips the header row by default, treating subsequent rows as content.
    Row content is joined using commas to maintain the original CSV structure.

    Example:
        For a CSV with content:
        name,age,city
        John,30,New York
        Mary,25,Boston
        
        This will generate two pages:
        Page 0: "John,30,New York"  (offset = 0)
        Page 1: "Mary,25,Boston"    (offset = length of first row + 1)
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Parse CSV content into Page objects asynchronously.

        Args:
            content (IO): The input content, which can be bytes, string, or a buffered reader.
                         Content will be automatically decoded if needed.

        Yields:
            Page: A series of Page objects, each representing one row from the CSV.
                 Page numbers start at 0 and increment sequentially.
                 Offsets account for the full content length of previous rows.

        Notes:
            - The header row is automatically skipped
            - Each row's fields are joined with commas in the output
            - Offset calculation includes newline characters
        """
        # Handle different input types by normalizing to string
        content_str: str
        if isinstance(content, (bytes, bytearray)):
            content_str = content.decode("utf-8")
        elif hasattr(content, "read"):  # Handle BufferedReader
            content_str = content.read().decode("utf-8")

        # Create CSV reader and prepare for processing
        reader = csv.reader(content_str.splitlines())
        offset = 0

        # Skip the header row to maintain existing behavior
        next(reader, None)

        # Process each row into a Page object
        for i, row in enumerate(reader):
            page_text = ",".join(row)
            yield Page(i, offset, page_text)
            # Increment offset by content length plus newline
            offset += len(page_text) + 1