import html
import logging
from typing import IO, AsyncGenerator, Union

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentTable
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from pypdf import PdfReader

from .page import Page
from .parser import Parser

logger = logging.getLogger("scripts")


class LocalPdfParser(Parser):
    """
    Parser implementation that uses PyPDF to extract text from PDF files locally.
    
    This parser provides basic PDF text extraction without requiring cloud services.
    It maintains document structure by:
    - Preserving page boundaries
    - Tracking text offsets
    - Processing pages sequentially
    
    While this parser is lighter weight than DocumentAnalysisParser, it offers
    simpler text extraction without advanced features like table recognition.
    """

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Extracts text from a PDF file using PyPDF.
        
        Args:
            content: IO stream containing PDF data
            
        Returns:
            AsyncGenerator yielding Page objects for each PDF page
            
        Notes:
            - Page numbers are zero-based
            - Offset tracks the cumulative text position across pages
            - Empty pages are included to maintain PDF structure
        """
        logger.info("Extracting text from '%s' using local PDF parser (pypdf)", content.name)

        reader = PdfReader(content)
        pages = reader.pages
        offset = 0
        for page_num, p in enumerate(pages):
            page_text = p.extract_text()
            yield Page(page_num=page_num, offset=offset, text=page_text)
            offset += len(page_text)


class DocumentAnalysisParser(Parser):
    """
    Parser implementation using Azure AI Document Intelligence for advanced document processing.
    
    This parser provides enhanced document understanding capabilities including:
    - Table structure recognition
    - Layout analysis
    - Form field detection
    - Multi-format support (PDF, DOCX, images, etc.)
    
    Features:
    - Converts tables to HTML format for better preservation
    - Maintains spatial relationships in documents
    - Handles complex document layouts
    - Supports multiple input document formats
    """

    def __init__(
        self, endpoint: str, credential: Union[AsyncTokenCredential, AzureKeyCredential], model_id="prebuilt-layout"
    ):
        """
        Initialize Document Intelligence parser.
        
        Args:
            endpoint: Azure Document Intelligence service endpoint
            credential: Azure authentication credential
            model_id: Model to use for analysis (default: prebuilt-layout)
        """
        self.model_id = model_id
        self.endpoint = endpoint
        self.credential = credential

    async def parse(self, content: IO) -> AsyncGenerator[Page, None]:
        """
        Processes document using Azure Document Intelligence service.
        
        Args:
            content: IO stream containing document data
            
        Returns:
            AsyncGenerator yielding Page objects with processed content
            
        Notes:
            - Tables are converted to HTML format within the text
            - Page numbers are zero-based
            - Maintains document layout and structure
        """
        logger.info("Extracting text from '%s' using Azure Document Intelligence", content.name)

        async with DocumentIntelligenceClient(
            endpoint=self.endpoint, credential=self.credential
        ) as document_intelligence_client:
            poller = await document_intelligence_client.begin_analyze_document(
                model_id=self.model_id, analyze_request=content, content_type="application/octet-stream"
            )
            form_recognizer_results = await poller.result()

            offset = 0
            for page_num, page in enumerate(form_recognizer_results.pages):
                tables_on_page = [
                    table
                    for table in (form_recognizer_results.tables or [])
                    if table.bounding_regions and table.bounding_regions[0].page_number == page_num + 1
                ]

                # mark all positions of the table spans in the page
                page_offset = page.spans[0].offset
                page_length = page.spans[0].length
                table_chars = [-1] * page_length
                for table_id, table in enumerate(tables_on_page):
                    for span in table.spans:
                        # replace all table spans with "table_id" in table_chars array
                        for i in range(span.length):
                            idx = span.offset - page_offset + i
                            if idx >= 0 and idx < page_length:
                                table_chars[idx] = table_id

                # build page text by replacing characters in table spans with table html
                page_text = ""
                added_tables = set()
                for idx, table_id in enumerate(table_chars):
                    if table_id == -1:
                        page_text += form_recognizer_results.content[page_offset + idx]
                    elif table_id not in added_tables:
                        page_text += DocumentAnalysisParser.table_to_html(tables_on_page[table_id])
                        added_tables.add(table_id)

                yield Page(page_num=page_num, offset=offset, text=page_text)
                offset += len(page_text)

    @classmethod
    def table_to_html(cls, table: DocumentTable):
        """
        Converts a Document Intelligence table to HTML format.
        
        Args:
            table: Document Intelligence table object
            
        Returns:
            str: HTML representation of the table
            
        Features:
            - Preserves table structure (rows, columns)
            - Handles column and row spans
            - Distinguishes headers from regular cells
            - Escapes HTML in cell content
        """
        table_html = "<table>"
        rows = [
            sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index)
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
                cell_spans = ""
                if cell.column_span is not None and cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span is not None and cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html