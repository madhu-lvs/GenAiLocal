import asyncio
import logging
import os
from typing import List, Optional

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchVectorizer,
)

from .blobmanager import BlobManager
from .embeddings import OpenAIEmbeddings
from .listfilestrategy import File
from .strategy import SearchInfo
from .textsplitter import SplitPage

logger = logging.getLogger("scripts")


class Section:
    """
    A processed document section prepared for search indexing.
    
    Bridges document processing and search indexing by connecting raw content
    with its processed sections and optional categorization metadata.
    """

    def __init__(self, split_page: SplitPage, content: File, category: Optional[str] = None):
        self.split_page = split_page
        self.content = content
        self.category = category


class SearchManager:
    """
    Azure AI Search index manager supporting content indexing and search operations.
    
    Provides comprehensive search service management including index creation,
    vector search configuration, semantic search setup, content ingestion,
    and security integration through access control lists.
    """

    def __init__(
        self,
        search_info: SearchInfo,
        search_analyzer_name: Optional[str] = None,
        use_acls: bool = False,
        use_int_vectorization: bool = False,
        embeddings: Optional[OpenAIEmbeddings] = None,
        search_images: bool = False,
    ):
        self.search_info = search_info
        self.search_analyzer_name = search_analyzer_name
        self.use_acls = use_acls
        self.use_int_vectorization = use_int_vectorization
        self.embeddings = embeddings
        self.embedding_dimensions = self.embeddings.open_ai_dimensions if self.embeddings else 1536
        self.search_images = search_images

    async def create_index(self, vectorizers: Optional[List[VectorSearchVectorizer]] = None):
        """
        Creates or updates the search index with specified configuration including
        field definitions, vector search settings, and security fields if enabled.
        """
        logger.info("Ensuring search index %s exists", self.search_info.index_name)

        async with self.search_info.create_search_index_client() as search_index_client:
            fields = [
                (
                    SimpleField(name="id", type="Edm.String", key=True)
                    if not self.use_int_vectorization
                    else SearchField(
                        name="id",
                        type="Edm.String",
                        key=True,
                        sortable=True,
                        filterable=True,
                        facetable=True,
                        analyzer_name="keyword",
                    )
                ),
                SearchableField(
                    name="content",
                    type="Edm.String",
                    analyzer_name=self.search_analyzer_name,
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    hidden=False,
                    searchable=True,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    vector_search_dimensions=self.embedding_dimensions,
                    vector_search_profile_name="embedding_config",
                ),
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(
                    name="sourcepage",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="sourcefile",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="storageUrl",
                    type="Edm.String",
                    filterable=True,
                    facetable=False,
                ),
            ]
            if self.use_acls:
                fields.append(
                    SimpleField(
                        name="oids",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                        filterable=True,
                    )
                )
                fields.append(
                    SimpleField(
                        name="groups",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                        filterable=True,
                    )
                )
            if self.use_int_vectorization:
                fields.append(SearchableField(name="parent_id", type="Edm.String", filterable=True))
            if self.search_images:
                fields.append(
                    SearchField(
                        name="imageEmbedding",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        hidden=False,
                        searchable=True,
                        filterable=False,
                        sortable=False,
                        facetable=False,
                        vector_search_dimensions=1024,
                        vector_search_profile_name="embedding_config",
                    ),
                )

            index = SearchIndex(
                name=self.search_info.index_name,
                fields=fields,
                semantic_search=SemanticSearch(
                    configurations=[
                        SemanticConfiguration(
                            name="default",
                            prioritized_fields=SemanticPrioritizedFields(
                                title_field=None, content_fields=[SemanticField(field_name="content")]
                            ),
                        )
                    ]
                ),
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(
                            name="hnsw_config",
                            parameters=HnswParameters(metric="cosine"),
                        )
                    ],
                    profiles=[
                        VectorSearchProfile(
                            name="embedding_config",
                            algorithm_configuration_name="hnsw_config",
                            vectorizer=(
                                f"{self.search_info.index_name}-vectorizer" if self.use_int_vectorization else None
                            ),
                        ),
                    ],
                    vectorizers=vectorizers,
                ),
            )
            if self.search_info.index_name not in [name async for name in search_index_client.list_index_names()]:
                logger.info("Creating %s search index", self.search_info.index_name)
                await search_index_client.create_index(index)
            else:
                logger.info("Search index %s already exists", self.search_info.index_name)
                index_definition = await search_index_client.get_index(self.search_info.index_name)
                if not any(field.name == "storageUrl" for field in index_definition.fields):
                    logger.info("Adding storageUrl field to index %s", self.search_info.index_name)
                    index_definition.fields.append(
                        SimpleField(
                            name="storageUrl",
                            type="Edm.String",
                            filterable=True,
                            facetable=False,
                        ),
                    )
                    await search_index_client.create_or_update_index(index_definition)

    async def update_content(
        self, sections: List[Section], image_embeddings: Optional[List[List[float]]] = None, url: Optional[str] = None
    ):
        """
        Updates search index with new or modified content, handling batch processing
        of sections with embeddings generation when configured.
        """
        MAX_BATCH_SIZE = 1000
        section_batches = [sections[i : i + MAX_BATCH_SIZE] for i in range(0, len(sections), MAX_BATCH_SIZE)]

        async with self.search_info.create_search_client() as search_client:
            for batch_index, batch in enumerate(section_batches):
                documents = [
                    {
                        "id": f"{section.content.filename_to_id()}-page-{section_index + batch_index * MAX_BATCH_SIZE}",
                        "content": section.split_page.text,
                        "category": section.category,
                        "sourcepage": (
                            BlobManager.blob_image_name_from_file_page(
                                filename=section.content.filename(),
                                page=section.split_page.page_num,
                            )
                            if image_embeddings
                            else BlobManager.sourcepage_from_file_page(
                                filename=section.content.filename(),
                                page=section.split_page.page_num,
                            )
                        ),
                        "sourcefile": section.content.filename(),
                        **section.content.acls,
                    }
                    for section_index, section in enumerate(batch)
                ]
                if url:
                    for document in documents:
                        document["storageUrl"] = url
                if self.embeddings:
                    embeddings = await self.embeddings.create_embeddings(
                        texts=[section.split_page.text for section in batch]
                    )
                    for i, document in enumerate(documents):
                        document["embedding"] = embeddings[i]
                if image_embeddings:
                    for i, (document, section) in enumerate(zip(documents, batch)):
                        document["imageEmbedding"] = image_embeddings[section.split_page.page_num]

                await search_client.upload_documents(documents)

    async def remove_content(self, path: Optional[str] = None, only_oid: Optional[str] = None):
        """
        Removes content from the search index based on path and ownership criteria.
        Handles batch deletion with appropriate delays for index updates.
        """
        logger.info(
            "Removing sections from '{%s or '<all>'}' from search index '%s'", path, self.search_info.index_name
        )
        async with self.search_info.create_search_client() as search_client:
            while True:
                filter = None
                if path is not None:
                    logger.info("path is not none, path: %s", path)
                    path_for_filter = os.path.basename(path).replace("'", "''")
                    filter = f"sourcepage eq '{path_for_filter}'"
                max_results = 1000
                result = await search_client.search(
                    search_text="", filter=filter, top=max_results, include_total_count=True
                )
                result_count = await result.get_count()
                logger.info("result_count: %d", result_count)
                if result_count == 0:
                    break
                documents_to_remove = []
                async for document in result:
                    logger.info("document_id: %s", document["id"])
                    if not only_oid or document.get("oids") == [only_oid]:
                        documents_to_remove.append({"id": document["id"]})
                logger.info("documents_to_remove: %s", documents_to_remove)
                if len(documents_to_remove) == 0:
                    if result_count < max_results:
                        break
                    else:
                        continue
                removed_docs = await search_client.delete_documents(documents_to_remove)
                logger.info("Removed %d sections from index", len(removed_docs))
                await asyncio.sleep(2)