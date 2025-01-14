import logging
from typing import List, Optional
from datetime import timedelta
from .blobmanager import BlobManager
from .embeddings import ImageEmbeddings, OpenAIEmbeddings
from .fileprocessor import FileProcessor
from .listfilestrategy import File, ListFileStrategy
from .searchmanager import SearchManager, Section
from .strategy import DocumentAction, SearchInfo, Strategy
from azure.search.documents.indexes.models import (
    FieldMapping,
    SearchIndexer,
    IndexingSchedule
)

logger = logging.getLogger("scripts")
async def parse_file(
    file: File,
    file_processors: dict[str, FileProcessor],
    category: Optional[str] = None,
    image_embeddings: Optional[ImageEmbeddings] = None,
) -> List[Section]:
    key = file.file_extension().lower()
    processor = file_processors.get(key)
    if processor is None:
        logger.info("Skipping '%s', no parser found.", file.filename())
        return []
    logger.info("Ingesting '%s'", file.filename())
    pages = [page async for page in processor.parser.parse(content=file.content)]
    logger.info("Splitting '%s' into sections", file.filename())
    if image_embeddings:
        logger.warning("Each page will be split into smaller chunks of text, but images will be of the entire page.")
    sections = [
        Section(split_page, content=file, category=category) for split_page in processor.splitter.split_pages(pages)
    ]
    return sections


class FileStrategy(Strategy):
    """
    Strategy for ingesting documents into a search service from files stored either locally or in Azure Data Lake Storage.
    
    This class implements the core document processing pipeline, handling the entire flow from raw files to
    searchable content in Azure Cognitive Search. It coordinates multiple components including:
    - Document parsing and chunking
    - Text and image embedding generation
    - Search index management
    - Access control integration
    
    The strategy supports different document actions (Add/Remove/RemoveAll) and can work with both
    text-based and vision-based embedding models.

    Attributes:
        list_file_strategy (ListFileStrategy): Strategy for listing source files
        blob_manager (BlobManager): Handles Azure Blob Storage operations
        file_processors (dict[str, FileProcessor]): Maps file extensions to their processors
        document_action (DocumentAction): Specifies the action to perform (Add/Remove/RemoveAll)
        embeddings (Optional[OpenAIEmbeddings]): Service for generating text embeddings
        image_embeddings (Optional[ImageEmbeddings]): Service for generating image embeddings
        search_analyzer_name (Optional[str]): Name of the search analyzer to use
        search_info (SearchInfo): Configuration for the search service
        use_acls (bool): Whether to enforce access control lists
        category (Optional[str]): Category label for ingested documents
    """

    def __init__(
        self,
        list_file_strategy: ListFileStrategy,
        blob_manager: BlobManager,
        search_info: SearchInfo,
        file_processors: dict[str, FileProcessor],
        document_action: DocumentAction = DocumentAction.Add,
        embeddings: Optional[OpenAIEmbeddings] = None,
        image_embeddings: Optional[ImageEmbeddings] = None,
        search_analyzer_name: Optional[str] = None,
        use_acls: bool = False,
        category: Optional[str] = None,
    ):
        """
        Initialize a new FileStrategy instance.

        Args:
            list_file_strategy: Strategy for listing source files
            blob_manager: Manager for Azure Blob Storage operations
            search_info: Configuration for the search service
            file_processors: Dictionary mapping file extensions to their processors
            document_action: Action to perform (default: DocumentAction.Add)
            embeddings: Service for generating text embeddings (optional)
            image_embeddings: Service for generating image embeddings (optional)
            search_analyzer_name: Name of the search analyzer (optional)
            use_acls: Whether to enforce access control lists (default: False)
            category: Category label for ingested documents (optional)
        """
        self.list_file_strategy = list_file_strategy
        self.blob_manager = blob_manager
        self.file_processors = file_processors
        self.document_action = document_action
        self.embeddings = embeddings
        self.image_embeddings = image_embeddings
        self.search_analyzer_name = search_analyzer_name
        self.search_info = search_info
        self.use_acls = use_acls
        self.category = category

    async def setup(self):
            """
            Initialize the search index with required fields and configurations.
            
            This method ensures the search index exists and is properly configured for:
            - Text and vector search capabilities
            - Access control field requirements
            - Image embedding support if enabled
            
            The index configuration respects:
            - Analyzer settings
            - ACL requirements
            - Vector search dimensions
            - Image search capabilities
            """
            search_manager = SearchManager(
                self.search_info,
                self.search_analyzer_name,
                self.use_acls,
                False,
                self.embeddings,
                search_images=self.image_embeddings is not None,
            )
            await search_manager.create_index()

    async def run(self):
        """
        Execute the file processing strategy based on the configured document action.
        
        This method orchestrates the document processing pipeline:
        - For DocumentAction.Add: Process and index new documents
        - For DocumentAction.Remove: Remove specified documents
        - For DocumentAction.RemoveAll: Clear all documents
        
        The process includes:
        1. File listing and processing
        2. Blob storage management
        3. Embedding generation (if configured)
        4. Search index updates
        
        Error handling ensures logging of issues while maintaining processing flow.
        """
        search_manager = SearchManager(
            self.search_info, self.search_analyzer_name, self.use_acls, False, self.embeddings
        )
        if self.document_action == DocumentAction.Add:
            files = self.list_file_strategy.list()
            async for file in files:
                try:
                    sections = await parse_file(file, self.file_processors, self.category, self.image_embeddings)
                    if sections:
                        blob_sas_uris = await self.blob_manager.upload_blob(file)
                        blob_image_embeddings: Optional[List[List[float]]] = None
                        if self.image_embeddings and blob_sas_uris:
                            blob_image_embeddings = await self.image_embeddings.create_embeddings(blob_sas_uris)
                        await search_manager.update_content(sections, blob_image_embeddings, url=file.url)
                finally:
                    if file:
                        file.close()
        elif self.document_action == DocumentAction.Remove:
            paths = self.list_file_strategy.list_paths()
            async for path in paths:
                await self.blob_manager.remove_blob(path)
                await search_manager.remove_content(path)
        elif self.document_action == DocumentAction.RemoveAll:
            await self.blob_manager.remove_blob()
            await search_manager.remove_content()

class UploadUserFileStrategy:
    """
    Strategy for processing and indexing files that users have uploaded to Azure Data Lake Storage Gen2.
    
    This class provides a specialized pipeline for handling user-uploaded documents, including:
    - Secure file processing with user-specific ACLs
    - Integration with the search index
    - Support for text embeddings
    
    The strategy ensures that:
    - Files are properly associated with the uploading user
    - Access controls are maintained
    - Content is searchable within the user's context

    Note:
        This strategy currently does not support image embeddings for user-uploaded content.
    """

    def __init__(
        self,
        search_info: SearchInfo,
        file_processors: dict[str, FileProcessor],
        embeddings: Optional[OpenAIEmbeddings] = None,
        image_embeddings: Optional[ImageEmbeddings] = None,
    ):
        """
        Initialize a new UploadUserFileStrategy instance.

        Args:
            search_info: Configuration for the search service
            file_processors: Dictionary mapping file extensions to their processors
            embeddings: Service for generating text embeddings (optional)
            image_embeddings: Service for generating image embeddings (optional)
                Note: Currently not supported for user uploads
        """
        self.file_processors = file_processors
        self.embeddings = embeddings
        self.image_embeddings = image_embeddings
        self.search_info = search_info
        self.search_manager = SearchManager(self.search_info, None, True, False, self.embeddings)

    async def add_file(self, file: File):
        """
        Process and index a user-uploaded file.
        
        Args:
            file: The file to process, including content and ACL information
            
        Note:
            Image embeddings are not currently supported for user uploads.
            A warning will be logged if image embeddings are configured.
        """
        if self.image_embeddings:
            logging.warning("Image embeddings are not currently supported for the user upload feature")
        sections = await parse_file(file, self.file_processors)
        if sections:
            await self.search_manager.update_content(sections, url=file.url)

    async def remove_file(self, filename: str, oid: Optional[str] = None):
        """
        Remove a user-uploaded file from the search index.
        
        Args:
            filename: Name of the file to remove
            oid: Object ID of the user who owns the file
            
        Note:
            This operation only affects the search index, not the stored file.
        """
        if filename is None or filename == "":
            logging.warning("Filename is required to remove a file")
            return
        await self.search_manager.remove_content(filename, oid)

    async def rerun_indexer(self, reset: bool = False):
        """
            updated, resets and run an indexer to rebuild the index
        """
        
        indexer_name = f"{self.search_info.index_name}-indexer"
        schedule = IndexingSchedule(interval=timedelta(hours=4))

        indexer = SearchIndexer(
            name=indexer_name,
            description="Indexer to index documents and generate embeddings",
            skillset_name=f"{self.search_info.index_name}-skillset",
            target_index_name=self.search_info.index_name,
            data_source_name=f"{self.search_info.index_name}-blob",
            field_mappings=[FieldMapping(source_field_name="metadata_storage_name", target_field_name="title")],
            schedule=schedule
        )

        indexer_client = self.search_info.create_search_indexer_client()
        indexer_result = await indexer_client.create_or_update_indexer(indexer)

        if reset:
            await indexer_client.reset_indexer(indexer_name)
        
        await indexer_client.run_indexer(indexer_name)
        await indexer_client.close()

        logger.info(
            f"Successfully rebuild index, indexer: {indexer_result.name}, and skillset. Please navigate to search service in Azure Portal to view the status of the indexer."
        )