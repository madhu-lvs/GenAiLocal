import os
from abc import ABC
from dataclasses import dataclass
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    List,
    Optional,
    TypedDict,
    cast,
)
from urllib.parse import urljoin

import aiohttp
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import (
    QueryCaptionResult,
    QueryType,
    VectorizedQuery,
    VectorQuery,
)
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from core.authentication import AuthenticationHelper
from text import nonewlines

@dataclass
class Document:
    """
    Represents a document retrieved from the search index with its associated metadata and scores.
    
    Attributes:
        id: Unique identifier for the document
        content: The actual text content of the document
        embedding: Vector embedding of the text content
        image_embedding: Vector embedding of any associated image
        category: Classification category of the document 
        sourcepage: Original source page identifier
        sourcefile: Original source file name
        oids: List of object IDs with access permissions
        groups: List of group IDs with access permissions
        captions: Extracted captions from semantic search
        score: Search relevance score
        reranker_score: Score from semantic reranking
    """
    id: Optional[str]
    content: Optional[str] 
    embedding: Optional[List[float]]
    image_embedding: Optional[List[float]]
    category: Optional[str]
    sourcepage: Optional[str]
    sourcefile: Optional[str]
    oids: Optional[List[str]]
    groups: Optional[List[str]]
    captions: List[QueryCaptionResult]
    score: Optional[float] = None
    reranker_score: Optional[float] = None

    def serialize_for_results(self) -> dict[str, Any]:
        """
        Serializes the document into a dictionary format suitable for search results.
        Handles proper formatting of embeddings and captions.
        """
        return {
            "id": self.id,
            "content": self.content,
            "embedding": Document.trim_embedding(self.embedding),
            "imageEmbedding": Document.trim_embedding(self.image_embedding), 
            "category": self.category,
            "sourcepage": self.sourcepage,
            "sourcefile": self.sourcefile,
            "oids": self.oids,
            "groups": self.groups,
            "captions": (
                [
                    {
                        "additional_properties": caption.additional_properties,
                        "text": caption.text,
                        "highlights": caption.highlights,
                    }
                    for caption in self.captions
                ]
                if self.captions
                else []
            ),
            "score": self.score,
            "reranker_score": self.reranker_score,
        }

    @classmethod
    def trim_embedding(cls, embedding: Optional[List[float]]) -> Optional[str]:
        """
        Returns a trimmed representation of vector embeddings for display purposes.
        Shows first 2 values plus count of remaining dimensions.
        """
        if embedding:
            if len(embedding) > 2:
                return f"[{embedding[0]}, {embedding[1]} ...+{len(embedding) - 2} more]"
            else:
                return str(embedding)
        return None

@dataclass 
class ThoughtStep:
    """
    Represents a single step in the chain-of-thought reasoning process.
    Used for logging and debugging the RAG pipeline steps.
    """
    title: str
    description: Optional[Any]
    props: Optional[dict[str, Any]] = None

class Approach(ABC):
    """
    Abstract base class defining the core RAG functionality for retrieving and processing documents.
    Implements shared logic for search, embedding generation, and access control.
    """
    # Allows usage of non-GPT models that may not have accurate token counting
    ALLOW_NON_GPT_MODELS = True

    def __init__(
        self,
        search_client: SearchClient,
        openai_client: AsyncOpenAI,
        auth_helper: AuthenticationHelper,
        query_language: Optional[str],
        query_speller: Optional[str], 
        embedding_deployment: Optional[str],
        embedding_model: str,
        embedding_dimensions: int,
        openai_host: str,
        vision_endpoint: str,
        vision_token_provider: Callable[[], Awaitable[str]],
    ):
        """
        Initialize the base RAG approach with required clients and configuration.
        
        Args:
            search_client: Azure Cognitive Search client
            openai_client: Azure OpenAI or OpenAI client
            auth_helper: Helper for authentication and authorization
            query_language: Language code for search queries
            query_speller: Spelling correction mode
            embedding_deployment: Azure OpenAI embedding deployment name
            embedding_model: Name of embedding model to use
            embedding_dimensions: Dimension of embedding vectors
            openai_host: OpenAI API host
            vision_endpoint: Computer vision API endpoint
            vision_token_provider: Callback to get vision API tokens
        """
        self.search_client = search_client
        self.openai_client = openai_client
        self.auth_helper = auth_helper
        self.query_language = query_language
        self.query_speller = query_speller
        self.embedding_deployment = embedding_deployment
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.openai_host = openai_host
        self.vision_endpoint = vision_endpoint
        self.vision_token_provider = vision_token_provider

    def build_filter(self, overrides: dict[str, Any], auth_claims: dict[str, Any]) -> Optional[str]:
        """
        Builds an OData filter expression for search queries based on category exclusions
        and security permissions from auth claims.
        """
        exclude_category = overrides.get("exclude_category")
        security_filter = self.auth_helper.build_security_filters(overrides, auth_claims)
        filters = []
        if exclude_category:
            filters.append("category ne '{}'".format(exclude_category.replace("'", "''")))
        if security_filter:
            filters.append(security_filter)
        return None if len(filters) == 0 else " and ".join(filters)

    async def search(
        self,
        top: int,
        query_text: Optional[str],
        filter: Optional[str],
        vectors: List[VectorQuery],
        use_text_search: bool,
        use_vector_search: bool,
        use_semantic_ranker: bool,
        use_semantic_captions: bool,
        minimum_search_score: Optional[float],
        minimum_reranker_score: Optional[float],
    ) -> List[Document]:
        """
        Performs a search against the Azure Cognitive Search index using the specified parameters.
        Supports hybrid search combining text, vector and semantic search capabilities.
        
        Returns filtered list of Document objects meeting the minimum score thresholds.
        """
        search_text = query_text if use_text_search else ""
        search_vectors = vectors if use_vector_search else []
        
        if use_semantic_ranker:
            results = await self.search_client.search(
                search_text=search_text,
                filter=filter,
                top=top,
                query_caption="extractive|highlight-false" if use_semantic_captions else None,
                vector_queries=search_vectors,
                query_type=QueryType.SEMANTIC,
                query_language=self.query_language,
                query_speller=self.query_speller,
                semantic_configuration_name="default",
                semantic_query=query_text,
            )
        else:
            results = await self.search_client.search(
                search_text=search_text,
                filter=filter,
                top=top,
                vector_queries=search_vectors,
            )

        documents = []
        async for page in results.by_page():
            async for document in page:
                documents.append(
                    Document(
                        id=document.get("id"),
                        content=document.get("content"),
                        embedding=document.get("embedding"),
                        image_embedding=document.get("imageEmbedding"),
                        category=document.get("category"),
                        sourcepage=document.get("sourcepage"),
                        sourcefile=document.get("sourcefile"),
                        oids=document.get("oids"),
                        groups=document.get("groups"),
                        captions=cast(List[QueryCaptionResult], document.get("@search.captions")),
                        score=document.get("@search.score"),
                        reranker_score=document.get("@search.reranker_score"),
                    )
                )

            qualified_documents = [
                doc
                for doc in documents
                if (
                    (doc.score or 0) >= (minimum_search_score or 0)
                    and (doc.reranker_score or 0) >= (minimum_reranker_score or 0)
                )
            ]

        return qualified_documents

    def get_sources_content(
        self, results: List[Document], use_semantic_captions: bool, use_image_citation: bool
    ) -> list[str]:
        """
        Extracts formatted content from search results, either using semantic captions
        or full document content with proper citations.
        """
        if use_semantic_captions:
            return [
                (self.get_citation((doc.sourcepage or ""), use_image_citation))
                + ": "
                + nonewlines(" . ".join([cast(str, c.text) for c in (doc.captions or [])]))
                for doc in results
            ]
        else:
            return [
                (self.get_citation((doc.sourcepage or ""), use_image_citation)) + ": " + nonewlines(doc.content or "")
                for doc in results
            ]

    def get_citation(self, sourcepage: str, use_image_citation: bool) -> str:
        """
        Formats source citations for documents. Handles both PDF page references
        and direct image citations.
        """
        if use_image_citation:
            return sourcepage
        else:
            path, ext = os.path.splitext(sourcepage)
            if ext.lower() == ".png":
                page_idx = path.rfind("-")
                page_number = int(path[page_idx + 1:])
                return f"{path[:page_idx]}.pdf#page={page_number}"
            return sourcepage

    async def compute_text_embedding(self, q: str):
        """
        Generates text embeddings using the configured embedding model.
        Handles different models and dimensions based on configuration.
        """
        SUPPORTED_DIMENSIONS_MODEL = {
            "text-embedding-ada-002": False,
            "text-embedding-3-small": True,
            "text-embedding-3-large": True,
        }

        class ExtraArgs(TypedDict, total=False):
            dimensions: int

        dimensions_args: ExtraArgs = (
            {"dimensions": self.embedding_dimensions} if SUPPORTED_DIMENSIONS_MODEL[self.embedding_model] else {}
        )
        embedding = await self.openai_client.embeddings.create(
            model=self.embedding_deployment if self.embedding_deployment else self.embedding_model,
            input=q,
            **dimensions_args,
        )
        query_vector = embedding.data[0].embedding
        return VectorizedQuery(vector=query_vector, k_nearest_neighbors=50, fields="embedding")

    async def compute_image_embedding(self, q: str):
        """
        Generates image embeddings using Azure Computer Vision API.
        Used for image-based similarity search.
        """
        endpoint = urljoin(self.vision_endpoint, "computervision/retrieval:vectorizeText")
        headers = {"Content-Type": "application/json"}
        params = {"api-version": "2023-02-01-preview", "modelVersion": "latest"}
        data = {"text": q}

        headers["Authorization"] = "Bearer " + await self.vision_token_provider()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=endpoint, params=params, headers=headers, json=data, raise_for_status=True
            ) as response:
                json = await response.json()
                image_query_vector = json["vector"]
        return VectorizedQuery(vector=image_query_vector, k_nearest_neighbors=50, fields="imageEmbedding")

    async def run(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """
        Abstract method to be implemented by concrete approach classes.
        Executes the core RAG logic for processing a conversation turn.
        """
        raise NotImplementedError

    async def run_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Abstract method to be implemented by concrete approach classes.
        Executes the core RAG logic with streaming responses.
        """
        raise NotImplementedError