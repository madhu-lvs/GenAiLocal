from dataclasses import dataclass
from typing import Any

from .parser import Parser
from .textsplitter import TextSplitter


@dataclass(frozen=True)
class FileProcessor:
    """
    A container class that pairs a Parser with a TextSplitter to process documents.
    
    This class is responsible for managing the full document processing pipeline by combining:
    1. A parser that extracts text from specific document formats
    2. A text splitter that segments the extracted text into manageable chunks
    
    The class is immutable (frozen=True) to ensure thread safety and prevent accidental modifications
    during document processing.
    
    Attributes:
        parser (Parser): An instance of a Parser class that can extract text from a specific
            document format (e.g., PDF, HTML, Text). The parser handles the initial document
            processing and text extraction.
            
        splitter (TextSplitter): An instance of a TextSplitter class that handles breaking
            the extracted text into appropriate segments. This is crucial for maintaining
            chunk sizes that are compatible with embedding and indexing requirements.
    
    Example:
        pdf_parser = LocalPdfParser()
        text_splitter = SentenceTextSplitter(has_image_embeddings=False)
        processor = FileProcessor(parser=pdf_parser, splitter=text_splitter)
    
    Note:
        This class is designed to be used as part of a larger document processing pipeline,
        typically in conjunction with the broader indexing and search infrastructure.
    """
    
    parser: Parser
    splitter: TextSplitter