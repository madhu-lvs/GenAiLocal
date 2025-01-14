import json
from typing import IO, AsyncGenerator

from .page import Page
from .parser import Parser


class JsonParser(Parser):
    """
    A specialized parser that converts JSON content into Page objects for indexing and search.
    
    This parser handles two main JSON formats:
    1. Single JSON object: Converted into a single Page
    2. JSON array of objects: Each array item becomes a separate Page
    
    The parser maintains document structure by:
    - Preserving the original JSON formatting for each object
    - Tracking offset positions for array elements
    - Assigning sequential page numbers for array items
    
    Inherits from:
        Parser: Abstract base class defining the parsing interface
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Parses JSON content into one or more Page objects.
        
        Args:
            content: IO stream containing the JSON data to parse
            
        Returns:
            AsyncGenerator yielding Page objects, where each Page represents either:
            - A complete JSON object (for single objects)
            - An individual array element (for JSON arrays)
            
        The offset tracking ensures proper position indexing when:
        - Processing array elements sequentially 
        - Accounting for commas and brackets between elements
        """
        offset = 0
        data = json.loads(content.read())
        if isinstance(data, list):
            for i, obj in enumerate(data):
                offset += 1  # For opening bracket or comma before object
                page_text = json.dumps(obj)
                yield Page(i, offset, page_text)
                offset += len(page_text)
        elif isinstance(data, dict):
            yield Page(0, 0, json.dumps(data))