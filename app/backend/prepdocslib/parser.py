from abc import ABC
from typing import IO, AsyncGenerator

from .page import Page


class Parser(ABC):
    """
    Abstract base class defining the interface for document parsing operations.
    
    This class serves as the foundation for all document parsers in the system, 
    establishing a consistent interface for transforming various document formats 
    into a sequence of Page objects. It's designed to support:
    
    - Consistent parsing interface across document types (PDF, HTML, text, etc.)
    - Asynchronous streaming of page content
    - Stateless parsing operations
    - Extensible parser implementations
    
    All concrete parser implementations must provide an async parse() method that
    converts document content into a stream of Page objects, allowing for efficient
    processing of large documents without loading entire contents into memory.
    
    Usage:
        Concrete implementations should inherit this class and implement parse():
        
        class ConcreteParser(Parser):
            async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
                # Implementation specific to document format
                pass
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Parses document content into a stream of Page objects.
        
        Args:
            content: An IO stream containing the document content to parse
            
        Returns:
            AsyncGenerator yielding Page objects representing document sections
            
        Note:
            This is an abstract method that must be implemented by concrete parsers.
            The if/yield is present only to satisfy mypy type checking requirements.
        """
        if False:  # pragma: no cover - this is necessary for mypy to type check
            yield