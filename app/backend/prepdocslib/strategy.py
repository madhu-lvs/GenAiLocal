"""
Azure Search Integration Strategy Module

This module provides abstract base classes and core functionality for integrating with Azure Cognitive Search.
It defines the foundational components needed for document processing and search operations.

Key Components:
- SearchInfo: Configuration class for Azure Search service connections
- DocumentAction: Enum defining available document processing actions
- Strategy: Abstract base class defining the interface for search integration strategies

The module is designed to be extended by concrete implementations that provide specific 
document processing and indexing behaviors.
"""

import logging
from abc import ABC
from enum import Enum
from typing import Union

from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient, SearchIndexerClient

# User agent string for Azure service requests
USER_AGENT = "opensourcerer/1.0.0"

logger = logging.getLogger(__name__)

class SearchInfo:
    """
    Configuration class for Azure Search service connections.
    
    This class encapsulates the connection details and credentials needed to interact
    with an Azure Cognitive Search service. It provides factory methods for creating
    various types of search clients.

    Attributes:
        endpoint (str): The Azure Search service endpoint URL
        credential (Union[AsyncTokenCredential, AzureKeyCredential]): Authentication credential
        index_name (str): Name of the search index to interact with

    Example:
        search_info = SearchInfo(
            endpoint="https://my-search-service.search.windows.net",
            credential=AzureKeyCredential("my-api-key"),
            index_name="my-index"
        )
        search_client = search_info.create_search_client()
    """

    def __init__(
        self, 
        endpoint: str, 
        credential: Union[AsyncTokenCredential, AzureKeyCredential], 
        index_name: str
    ) -> None:
        """
        Initialize a new SearchInfo instance.

        Args:
            endpoint: Azure Search service endpoint URL
            credential: Authentication credential (either async token or API key)
            index_name: Name of the search index
        """
        self.endpoint = endpoint
        self.credential = credential
        self.index_name = index_name

    def create_search_client(self) -> SearchClient:
        """
        Create a SearchClient instance for performing search operations.

        Returns:
            SearchClient: Configured client for the specified index
        """
        return SearchClient(
            endpoint=self.endpoint, 
            index_name=self.index_name, 
            credential=self.credential
        )

    def create_search_index_client(self) -> SearchIndexClient:
        """
        Create a SearchIndexClient instance for managing search indexes.

        Returns:
            SearchIndexClient: Configured client for index management
        """
        return SearchIndexClient(
            endpoint=self.endpoint, 
            credential=self.credential
        )

    def create_search_indexer_client(self) -> SearchIndexerClient:
        """
        Create a SearchIndexerClient instance for managing search indexers.

        Returns:
            SearchIndexerClient: Configured client for indexer management
        """
        return SearchIndexerClient(
            endpoint=self.endpoint, 
            credential=self.credential
        )


class DocumentAction(Enum):
    """
    Enumeration of available document processing actions.

    Defines the possible operations that can be performed on documents:
    - Add: Add new documents to the search index
    - Remove: Remove specific documents from the search index
    - RemoveAll: Remove all documents from the search index
    """
    Add = 0
    Remove = 1
    RemoveAll = 2


class Strategy(ABC):
    """
    Abstract base class defining the interface for search integration strategies.

    This class provides the foundation for implementing different approaches to
    processing and indexing documents in Azure Cognitive Search. Concrete implementations
    must provide the setup and run logic specific to their strategy.

    The strategy pattern allows for different document processing approaches while
    maintaining a consistent interface.
    """

    async def setup(self) -> None:
        """
        Perform any necessary initialization or setup for the strategy.

        This method should handle tasks such as:
        - Creating or updating search indexes
        - Setting up required resources
        - Validating configurations

        Must be implemented by concrete strategy classes.

        Raises:
            NotImplementedError: If the concrete class doesn't implement this method
        """
        raise NotImplementedError

    async def run(self) -> None:
        """
        Execute the main document processing logic for the strategy.

        This method should implement the core functionality such as:
        - Document ingestion
        - Content extraction
        - Search index updates
        - Error handling

        Must be implemented by concrete strategy classes.

        Raises:
            NotImplementedError: If the concrete class doesn't implement this method
        """
        raise NotImplementedError