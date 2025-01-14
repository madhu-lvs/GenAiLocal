"""
Text Splitting Module

This module provides functionality for splitting text content into manageable chunks
while preserving semantic meaning and context. It supports both sentence-aware and
simple length-based splitting strategies.

Key Components:
- TextSplitter: Abstract base class for text splitting strategies
- SentenceTextSplitter: Implementation that splits text while preserving sentence boundaries
- SimpleTextSplitter: Implementation that splits text based on character length
- Multiple language support including CJK (Chinese, Japanese, Korean) characters

The splitting process respects:
- Maximum token limits for language models
- Sentence boundaries where possible
- Overlap between sections for context preservation
- Special handling for tables and structured content
"""

import logging
from abc import ABC
from typing import Generator, List, Optional, Set

import tiktoken
from .page import Page, SplitPage

logger = logging.getLogger(__name__)

# Model configuration for tokenization
ENCODING_MODEL = "text-embedding-ada-002"

# Word break characters for different language groups
STANDARD_WORD_BREAKS: Set[str] = {
    ",", ";", ":", " ", "(", ")", "[", "]", 
    "{", "}", "\t", "\n"
}

# CJK (Chinese, Japanese, Korean) specific word breaks
# Based on W3C document: https://www.w3.org/TR/jlreq/#cl-01
CJK_WORD_BREAKS: Set[str] = {
    "、", "，", "；", "：", "（", "）", "【", "】",
    "「", "」", "『", "』", "〔", "〕", "〈", "〉",
    "《", "》", "〖", "〗", "〘", "〙", "〚", "〛",
    "〝", "〞", "〟", "〰", "–", "—", "'", "'",
    "‚", "‛", """, """, "„", "‟", "‹", "›"
}

# Sentence ending characters
STANDARD_SENTENCE_ENDINGS: Set[str] = {".", "!", "?"}

# CJK sentence endings based on JIS X 4051:2004
CJK_SENTENCE_ENDINGS: Set[str] = {
    "。", "！", "？", "‼", "⁇", "⁈", "⁉"
}

# Default configuration values
DEFAULT_OVERLAP_PERCENT = 10  # Recommended overlap between sections
DEFAULT_SECTION_LENGTH = 1000  # Target length for text sections


class TextSplitter(ABC):
    """
    Abstract base class defining the interface for text splitting strategies.
    
    Implementations must provide logic to split a list of pages into smaller
    chunks (SplitPage objects) according to their specific strategy.
    """

    def split_pages(self, pages: List[Page]) -> Generator[SplitPage, None, None]:
        """
        Split input pages into smaller chunks.

        Args:
            pages: List of Page objects to split

        Yields:
            Generator[SplitPage, None, None]: Stream of split page chunks
        """
        raise NotImplementedError


class SentenceTextSplitter(TextSplitter):
    """
    Text splitter that attempts to preserve sentence boundaries while splitting content.
    
    Features:
    - Respects sentence endings across multiple languages
    - Maintains context through section overlap
    - Special handling for tables and structured content
    - Token-aware splitting for ML model compatibility
    """

    def __init__(
        self, 
        has_image_embeddings: bool, 
        max_tokens_per_section: int = 500
    ):
        """
        Initialize the sentence-aware text splitter.

        Args:
            has_image_embeddings: Whether image embeddings are being used
            max_tokens_per_section: Maximum tokens allowed per section
        """
        self.sentence_endings = STANDARD_SENTENCE_ENDINGS.union(CJK_SENTENCE_ENDINGS)
        self.word_breaks = STANDARD_WORD_BREAKS.union(CJK_WORD_BREAKS)
        self.max_section_length = DEFAULT_SECTION_LENGTH
        self.sentence_search_limit = 100
        self.max_tokens_per_section = max_tokens_per_section
        self.section_overlap = int(self.max_section_length * DEFAULT_OVERLAP_PERCENT / 100)
        self.has_image_embeddings = has_image_embeddings
        self.tokenizer = tiktoken.encoding_for_model(ENCODING_MODEL)

    def split_page_by_max_tokens(
        self, 
        page_num: int, 
        text: str
    ) -> Generator[SplitPage, None, None]:
        """
        Split text recursively based on token count limits.
        
        Args:
            page_num: Page number for the split sections
            text: Text content to split
            
        Yields:
            SplitPage objects containing the split content
        """
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= self.max_tokens_per_section:
            yield SplitPage(page_num=page_num, text=text)
            return

        # Find optimal split point near the center
        start = len(text) // 2
        pos = 0
        boundary = len(text) // 3
        split_position = -1

        while start - pos > boundary:
            if text[start - pos] in self.sentence_endings:
                split_position = start - pos
                break
            elif text[start + pos] in self.sentence_endings:
                split_position = start + pos
                break
            pos += 1

        # Split text and process recursively
        if split_position > 0:
            first_half = text[:split_position + 1]
            second_half = text[split_position + 1:]
        else:
            middle = len(text) // 2
            overlap = int(len(text) * (DEFAULT_OVERLAP_PERCENT / 100))
            first_half = text[:middle + overlap]
            second_half = text[middle - overlap:]

        yield from self.split_page_by_max_tokens(page_num, first_half)
        yield from self.split_page_by_max_tokens(page_num, second_half)

    def split_pages(self, pages: List[Page]) -> Generator[SplitPage, None, None]:
        """
        Split multiple pages into sections while preserving sentence boundaries.
        
        Args:
            pages: List of Page objects to split
            
        Yields:
            SplitPage objects containing the split content
        """
        def find_page(offset: int) -> int:
            """Determine which page an offset belongs to."""
            num_pages = len(pages)
            for i in range(num_pages - 1):
                if offset >= pages[i].offset and offset < pages[i + 1].offset:
                    return pages[i].page_num
            return pages[num_pages - 1].page_num

        # Combine all text for processing
        all_text = "".join(page.text for page in pages)
        if not all_text.strip():
            return

        # Handle small content that doesn't need splitting
        if len(all_text) <= self.max_section_length:
            yield from self.split_page_by_max_tokens(
                page_num=find_page(0), 
                text=all_text
            )
            return

        # Process content in overlapping chunks
        start = 0
        length = len(all_text)
        
        while start + self.section_overlap < length:
            # Find section boundaries
            last_word = -1
            end = min(start + self.max_section_length, length)

            # Try to find sentence boundary
            while (end < length and 
                   (end - start - self.max_section_length) < self.sentence_search_limit and 
                   all_text[end] not in self.sentence_endings):
                if all_text[end] in self.word_breaks:
                    last_word = end
                end += 1

            # Fall back to word boundary if needed
            if end < length and all_text[end] not in self.sentence_endings and last_word > 0:
                end = last_word

            if end < length:
                end += 1

            # Find start of next section
            last_word = -1
            while (start > 0 and 
                   start > end - self.max_section_length - 2 * self.sentence_search_limit and 
                   all_text[start] not in self.sentence_endings):
                if all_text[start] in self.word_breaks:
                    last_word = start
                start -= 1

            if all_text[start] not in self.sentence_endings and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            yield from self.split_page_by_max_tokens(
                page_num=find_page(start), 
                text=section_text
            )

            # Handle unclosed tables
            last_table_start = section_text.rfind("<table")
            if (last_table_start > 2 * self.sentence_search_limit and 
                last_table_start > section_text.rfind("</table")):
                # Adjust next section start to include unclosed table
                start = min(
                    end - self.section_overlap,
                    start + last_table_start
                )
                logger.info(
                    f"Section ends with unclosed table, adjusting next section start point. "
                    f"Page: {find_page(start)}, Offset: {start}, Table start: {last_table_start}"
                )
            else:
                start = end - self.section_overlap

        # Handle final section if needed
        if start + self.section_overlap < end:
            yield from self.split_page_by_max_tokens(
                page_num=find_page(start),
                text=all_text[start:end]
            )


class SimpleTextSplitter(TextSplitter):
    """
    Basic text splitter that splits content based on character length.
    
    This splitter is suitable for cases where:
    - Sentence preservation is not critical
    - Simple length-based splitting is sufficient
    - Processing speed is prioritized over semantic coherence
    """

    def __init__(self, max_object_length: int = 1000):
        """
        Initialize the simple text splitter.

        Args:
            max_object_length: Maximum characters per section
        """
        self.max_object_length = max_object_length

    def split_pages(self, pages: List[Page]) -> Generator[SplitPage, None, None]:
        """
        Split pages into fixed-length sections.

        Args:
            pages: List of Page objects to split
            
        Yields:
            SplitPage objects of specified maximum length
        """
        all_text = "".join(page.text for page in pages)
        if not all_text.strip():
            return

        length = len(all_text)
        if length <= self.max_object_length:
            yield SplitPage(page_num=0, text=all_text)
            return

        # Split into chunks of max_object_length
        for i in range(0, length, self.max_object_length):
            yield SplitPage(
                page_num=i // self.max_object_length,
                text=all_text[i:i + self.max_object_length]
            )