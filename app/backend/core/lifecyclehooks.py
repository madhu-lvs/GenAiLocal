from typing import Union
from quart import Blueprint, current_app
from openai import AsyncAzureOpenAI, AsyncOpenAI
from azure.search.documents.aio import SearchClient
from core.authentication import AuthenticationHelper
import os
from prepdocs import (
    clean_key_if_exists,
    setup_embeddings_service,
    setup_file_processors,
    setup_search_info,
)
from azure.storage.blob.aio import ContainerClient
from prepdocslib.filestrategy import UploadUserFileStrategy
from approaches.chatreadretrievereadvision import ChatReadRetrieveReadVisionApproach
from approaches.retrievethenread import RetrieveThenReadApproach
from approaches.retrievethenreadvision import RetrieveThenReadVisionApproach
from azure.search.documents.indexes.aio import SearchIndexClient
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from azure.identity.aio import (
    AzureDeveloperCliCredential,
    ManagedIdentityCredential,
    get_bearer_token_provider,
)
from azure.storage.filedatalake.aio import FileSystemClient

from config import (
    CONFIG_ASK_APPROACH, 
    CONFIG_ASK_VISION_APPROACH, 
    CONFIG_AUTH_CLIENT, 
    CONFIG_BLOB_CONTAINER_CLIENT, 
    CONFIG_CHAT_APPROACH, 
    CONFIG_CHAT_HISTORY_BROWSER_ENABLED, 
    CONFIG_CHAT_VISION_APPROACH, 
    CONFIG_CREDENTIAL, 
    CONFIG_GPT4V_DEPLOYED, 
    CONFIG_INGESTER, 
    CONFIG_LANGUAGE_PICKER_ENABLED, 
    CONFIG_OPENAI_CLIENT, 
    CONFIG_SEARCH_CLIENT, 
    CONFIG_SEMANTIC_RANKER_DEPLOYED, 
    CONFIG_SPEECH_INPUT_ENABLED, 
    CONFIG_SPEECH_OUTPUT_AZURE_ENABLED, 
    CONFIG_SPEECH_OUTPUT_BROWSER_ENABLED, 
    CONFIG_SPEECH_SERVICE_ID, 
    CONFIG_SPEECH_SERVICE_LOCATION, 
    CONFIG_SPEECH_SERVICE_TOKEN, 
    CONFIG_SPEECH_SERVICE_VOICE,
    CONFIG_USER_BLOB_CONTAINER_CLIENT, 
    CONFIG_VECTOR_SEARCH_ENABLED
    )



def apply_lifecycle_hooks(bp: Blueprint):
    def setup_azure_credential():
        """
        Sets up Azure credentials based on environment configuration. It prioritizes the use of managed identity 
        if running on Azure. If a client ID or tenant ID is specified in the environment variables, they are used 
        accordingly for setting up the appropriate credential.

        Returns:
            azure_credential: The credential object for authenticating with Azure.
        """
        RUNNING_ON_AZURE = os.getenv("WEBSITE_HOSTNAME") is not None or os.getenv("RUNNING_IN_PRODUCTION") is not None
        AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

        if RUNNING_ON_AZURE:
            current_app.logger.info("Setting up Azure credential using ManagedIdentityCredential")
            if AZURE_CLIENT_ID:
                current_app.logger.info(
                    "Setting up Azure credential using ManagedIdentityCredential with client_id %s", AZURE_CLIENT_ID
                )
                azure_credential = ManagedIdentityCredential(client_id=AZURE_CLIENT_ID)
            else:
                current_app.logger.info("Setting up Azure credential using ManagedIdentityCredential")
                azure_credential = ManagedIdentityCredential()
        elif AZURE_TENANT_ID:
            current_app.logger.info(
                "Setting up Azure credential using AzureDeveloperCliCredential with tenant_id %s", AZURE_TENANT_ID
            )
            azure_credential = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID, process_timeout=60)
        else:
            current_app.logger.info("Setting up Azure credential using AzureDeveloperCliCredential for home tenant")
            azure_credential = AzureDeveloperCliCredential(process_timeout=60)

        return azure_credential

    def setup_openai_client(azure_credential: ManagedIdentityCredential | AzureDeveloperCliCredential) -> AsyncAzureOpenAI | AsyncOpenAI:
        """
        Sets up the OpenAI or Azure OpenAI client depending on the environment configuration.
        
        Args:
            azure_credential: The Azure credential used for passwordless authentication in Azure environments.
        
        Returns:
            openai_client: The configured OpenAI client instance.
        """
        USE_SPEECH_OUTPUT_AZURE = os.getenv("USE_SPEECH_OUTPUT_AZURE", False)
        OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
        AZURE_SPEECH_SERVICE_ID = os.getenv("AZURE_SPEECH_SERVICE_ID")
        AZURE_SPEECH_SERVICE_LOCATION = os.getenv("AZURE_SPEECH_SERVICE_LOCATION")
        AZURE_SPEECH_VOICE = os.getenv("AZURE_SPEECH_VOICE")
        AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
        AZURE_OPENAI_CUSTOM_URL = os.getenv("AZURE_OPENAI_CUSTOM_URL")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
        openai_client: AsyncAzureOpenAI | AsyncOpenAI
        
        # Set up Azure speech service if configured
        if USE_SPEECH_OUTPUT_AZURE:
            current_app.logger.info("USE_SPEECH_OUTPUT_AZURE is true, setting up Azure speech service")
            if not AZURE_SPEECH_SERVICE_ID or AZURE_SPEECH_SERVICE_ID == "":
                raise ValueError("Azure speech resource not configured correctly, missing AZURE_SPEECH_SERVICE_ID")
            if not AZURE_SPEECH_SERVICE_LOCATION or AZURE_SPEECH_SERVICE_LOCATION == "":
                raise ValueError("Azure speech resource not configured correctly, missing AZURE_SPEECH_SERVICE_LOCATION")
            current_app.config[CONFIG_SPEECH_SERVICE_ID] = AZURE_SPEECH_SERVICE_ID
            current_app.config[CONFIG_SPEECH_SERVICE_LOCATION] = AZURE_SPEECH_SERVICE_LOCATION
            current_app.config[CONFIG_SPEECH_SERVICE_VOICE] = AZURE_SPEECH_VOICE
            # Wait until token is needed to fetch for the first time
            current_app.config[CONFIG_SPEECH_SERVICE_TOKEN] = None
            current_app.config[CONFIG_CREDENTIAL] = azure_credential

        if OPENAI_HOST.startswith("azure"):
            api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
            if OPENAI_HOST == "azure_custom":
                current_app.logger.info("OPENAI_HOST is azure_custom, setting up Azure OpenAI custom client")
                if not AZURE_OPENAI_CUSTOM_URL:
                    raise ValueError("AZURE_OPENAI_CUSTOM_URL must be set when OPENAI_HOST is azure_custom")
                endpoint = AZURE_OPENAI_CUSTOM_URL
            else:
                current_app.logger.info("OPENAI_HOST is azure, setting up Azure OpenAI client")
                if not AZURE_OPENAI_SERVICE:
                    raise ValueError("AZURE_OPENAI_SERVICE must be set when OPENAI_HOST is azure")
                endpoint = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
            if api_key := os.getenv("AZURE_OPENAI_API_KEY_OVERRIDE"):
                current_app.logger.info("AZURE_OPENAI_API_KEY_OVERRIDE found, using as api_key for Azure OpenAI client")
                openai_client = AsyncAzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)
            else:
                current_app.logger.info("Using Azure credential (passwordless authentication) for Azure OpenAI client")
                token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
                openai_client = AsyncAzureOpenAI(
                    api_version=api_version,
                    azure_endpoint=endpoint,
                    azure_ad_token_provider=token_provider,
                )
        elif OPENAI_HOST == "local":
            current_app.logger.info("OPENAI_HOST is local, setting up local OpenAI client for OPENAI_BASE_URL with no key")
            openai_client = AsyncOpenAI(
                base_url=os.environ["OPENAI_BASE_URL"],
                api_key="no-key-required",
            )
        else:
            current_app.logger.info(
                "OPENAI_HOST is not azure, setting up OpenAI client using OPENAI_API_KEY and OPENAI_ORGANIZATION environment variables"
            )
            openai_client = AsyncOpenAI(
                api_key=OPENAI_API_KEY,
                organization=OPENAI_ORGANIZATION,
            )

        return openai_client

    @bp.before_app_serving
    async def setup_clients():
        # Replace these with your own values, either in environment variables or directly here
        AZURE_STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
        AZURE_STORAGE_CONTAINER = os.environ["AZURE_STORAGE_CONTAINER"]
        AZURE_SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
        AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
        # Shared by all OpenAI deployments
        OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
        OPENAI_CHATGPT_MODEL = os.environ["AZURE_OPENAI_CHATGPT_MODEL"]
        OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002")
        OPENAI_EMB_DIMENSIONS = int(os.getenv("AZURE_OPENAI_EMB_DIMENSIONS", 1536))
        # Used with Azure OpenAI deployments
        AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
        AZURE_OPENAI_GPT4V_DEPLOYMENT = os.environ.get("AZURE_OPENAI_GPT4V_DEPLOYMENT")
        AZURE_OPENAI_GPT4V_MODEL = os.environ.get("AZURE_OPENAI_GPT4V_MODEL")
        AZURE_OPENAI_CHATGPT_DEPLOYMENT = (
            os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
        )
        AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT") if OPENAI_HOST.startswith("azure") else None
        AZURE_OPENAI_CUSTOM_URL = os.getenv("AZURE_OPENAI_CUSTOM_URL")
        AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "")
        # Used only with non-Azure OpenAI deployments
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")

        AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        AZURE_USE_AUTHENTICATION = os.getenv("AZURE_USE_AUTHENTICATION", "").lower() == "true"
        AZURE_ENFORCE_ACCESS_CONTROL = os.getenv("AZURE_ENFORCE_ACCESS_CONTROL", "").lower() == "true"
        AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS = os.getenv("AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS", "").lower() == "true"
        AZURE_ENABLE_UNAUTHENTICATED_ACCESS = os.getenv("AZURE_ENABLE_UNAUTHENTICATED_ACCESS", "").lower() == "true"
        AZURE_SERVER_APP_ID = os.getenv("AZURE_SERVER_APP_ID")
        AZURE_SERVER_APP_SECRET = os.getenv("AZURE_SERVER_APP_SECRET")
        AZURE_CLIENT_APP_ID = os.getenv("AZURE_CLIENT_APP_ID")
        AZURE_AUTH_TENANT_ID = os.getenv("AZURE_AUTH_TENANT_ID", AZURE_TENANT_ID)

        AZURE_SEARCH_QUERY_LANGUAGE = os.getenv("AZURE_SEARCH_QUERY_LANGUAGE", "en-us")
        AZURE_SEARCH_QUERY_SPELLER = os.getenv("AZURE_SEARCH_QUERY_SPELLER", "lexicon")
        AZURE_SEARCH_SEMANTIC_RANKER = os.getenv("AZURE_SEARCH_SEMANTIC_RANKER", "free").lower()

        USE_GPT4V = os.getenv("USE_GPT4V", "").lower() == "true"
        ENABLE_LANGUAGE_PICKER = os.getenv("ENABLE_LANGUAGE_PICKER", "").lower() == "true"
        USE_SPEECH_INPUT_BROWSER = os.getenv("USE_SPEECH_INPUT_BROWSER", "").lower() == "true"
        USE_SPEECH_OUTPUT_BROWSER = os.getenv("USE_SPEECH_OUTPUT_BROWSER", "").lower() == "true"
        USE_SPEECH_OUTPUT_AZURE = os.getenv("USE_SPEECH_OUTPUT_AZURE", "").lower() == "true"
        USE_CHAT_HISTORY_BROWSER = os.getenv("USE_CHAT_HISTORY_BROWSER", "").lower() == "true"

        # Use the current user identity for keyless authentication to Azure services.
        # This assumes you use 'azd auth login' locally, and managed identity when deployed on Azure.
        # The managed identity is setup in the infra/ folder.
        azure_credential: Union[AzureDeveloperCliCredential, ManagedIdentityCredential]
        azure_credential = setup_azure_credential()

        # Set up clients for AI Search and Storage
        search_client = SearchClient(
            endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
            index_name=AZURE_SEARCH_INDEX,
            credential=azure_credential,
        )

        blob_container_client = ContainerClient(
            f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net", AZURE_STORAGE_CONTAINER, credential=azure_credential
        )

        # Set up authentication helper
        search_index = None
        if AZURE_USE_AUTHENTICATION:
            current_app.logger.info("AZURE_USE_AUTHENTICATION is true, setting up search index client")
            search_index_client = SearchIndexClient(
                endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
                credential=azure_credential,
            )
            search_index = await search_index_client.get_index(AZURE_SEARCH_INDEX)
            await search_index_client.close()
        auth_helper = AuthenticationHelper(
            search_index=search_index,
            use_authentication=AZURE_USE_AUTHENTICATION,
            server_app_id=AZURE_SERVER_APP_ID,
            server_app_secret=AZURE_SERVER_APP_SECRET,
            client_app_id=AZURE_CLIENT_APP_ID,
            tenant_id=AZURE_AUTH_TENANT_ID,
            require_access_control=AZURE_ENFORCE_ACCESS_CONTROL,
            enable_global_documents=AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS,
            enable_unauthenticated_access=AZURE_ENABLE_UNAUTHENTICATED_ACCESS,
        )

        if not AZURE_STORAGE_ACCOUNT or not AZURE_STORAGE_CONTAINER:
            raise ValueError(
                "AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_CONTAINER must be set"
            )
        user_blob_container_client = FileSystemClient(
            f"https://{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net",
            AZURE_STORAGE_CONTAINER,
            credential=azure_credential,
        )
        current_app.config[CONFIG_USER_BLOB_CONTAINER_CLIENT] = user_blob_container_client

        # Set up ingester
        file_processors = setup_file_processors(
            azure_credential=azure_credential,
            document_intelligence_service=os.getenv("AZURE_DOCUMENTINTELLIGENCE_SERVICE"),
            local_pdf_parser=os.getenv("USE_LOCAL_PDF_PARSER", "").lower() == "true",
            local_html_parser=os.getenv("USE_LOCAL_HTML_PARSER", "").lower() == "true",
            search_images=USE_GPT4V,
        )
        search_info = await setup_search_info(
            search_service=AZURE_SEARCH_SERVICE, index_name=AZURE_SEARCH_INDEX, azure_credential=azure_credential
        )
        text_embeddings_service = setup_embeddings_service(
            azure_credential=azure_credential,
            openai_host=OPENAI_HOST,
            openai_model_name=OPENAI_EMB_MODEL,
            openai_service=AZURE_OPENAI_SERVICE,
            openai_custom_url=AZURE_OPENAI_CUSTOM_URL,
            openai_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
            openai_dimensions=OPENAI_EMB_DIMENSIONS,
            openai_key=clean_key_if_exists(OPENAI_API_KEY),
            openai_org=OPENAI_ORGANIZATION,
            disable_vectors=os.getenv("USE_VECTORS", "").lower() == "false",
        )
        ingester = UploadUserFileStrategy(
            search_info=search_info, embeddings=text_embeddings_service, file_processors=file_processors
        )
        current_app.config[CONFIG_INGESTER] = ingester

        # Used by the OpenAI SDK
        openai_client: AsyncOpenAI
        openai_client = setup_openai_client(azure_credential=azure_credential)

        current_app.config[CONFIG_OPENAI_CLIENT] = openai_client
        current_app.config[CONFIG_SEARCH_CLIENT] = search_client
        current_app.config[CONFIG_BLOB_CONTAINER_CLIENT] = blob_container_client
        current_app.config[CONFIG_AUTH_CLIENT] = auth_helper

        current_app.config[CONFIG_GPT4V_DEPLOYED] = bool(USE_GPT4V)
        current_app.config[CONFIG_SEMANTIC_RANKER_DEPLOYED] = AZURE_SEARCH_SEMANTIC_RANKER != "disabled"
        current_app.config[CONFIG_VECTOR_SEARCH_ENABLED] = os.getenv("USE_VECTORS", "").lower() != "false"
        current_app.config[CONFIG_LANGUAGE_PICKER_ENABLED] = ENABLE_LANGUAGE_PICKER
        current_app.config[CONFIG_SPEECH_INPUT_ENABLED] = USE_SPEECH_INPUT_BROWSER
        current_app.config[CONFIG_SPEECH_OUTPUT_BROWSER_ENABLED] = USE_SPEECH_OUTPUT_BROWSER
        current_app.config[CONFIG_SPEECH_OUTPUT_AZURE_ENABLED] = USE_SPEECH_OUTPUT_AZURE
        current_app.config[CONFIG_CHAT_HISTORY_BROWSER_ENABLED] = USE_CHAT_HISTORY_BROWSER

        # Various approaches to integrate GPT and external knowledge, most applications will use a single one of these patterns
        # or some derivative, here we include several for exploration purposes
        current_app.config[CONFIG_ASK_APPROACH] = RetrieveThenReadApproach(
            search_client=search_client,
            openai_client=openai_client,
            auth_helper=auth_helper,
            chatgpt_model=OPENAI_CHATGPT_MODEL,
            chatgpt_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            embedding_model=OPENAI_EMB_MODEL,
            embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
            embedding_dimensions=OPENAI_EMB_DIMENSIONS,
            query_language=AZURE_SEARCH_QUERY_LANGUAGE,
            query_speller=AZURE_SEARCH_QUERY_SPELLER,
        )

        current_app.config[CONFIG_CHAT_APPROACH] = ChatReadRetrieveReadApproach(
            search_client=search_client,
            openai_client=openai_client,
            auth_helper=auth_helper,
            chatgpt_model=OPENAI_CHATGPT_MODEL,
            chatgpt_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            embedding_model=OPENAI_EMB_MODEL,
            embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
            embedding_dimensions=OPENAI_EMB_DIMENSIONS,
            query_language=AZURE_SEARCH_QUERY_LANGUAGE,
            query_speller=AZURE_SEARCH_QUERY_SPELLER,
        )

        if USE_GPT4V:
            current_app.logger.info("USE_GPT4V is true, setting up GPT4V approach")
            if not AZURE_OPENAI_GPT4V_MODEL:
                raise ValueError("AZURE_OPENAI_GPT4V_MODEL must be set when USE_GPT4V is true")
            token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")

            current_app.config[CONFIG_ASK_VISION_APPROACH] = RetrieveThenReadVisionApproach(
                search_client=search_client,
                openai_client=openai_client,
                blob_container_client=blob_container_client,
                auth_helper=auth_helper,
                vision_endpoint=AZURE_VISION_ENDPOINT,
                vision_token_provider=token_provider,
                gpt4v_deployment=AZURE_OPENAI_GPT4V_DEPLOYMENT,
                gpt4v_model=AZURE_OPENAI_GPT4V_MODEL,
                embedding_model=OPENAI_EMB_MODEL,
                embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
                embedding_dimensions=OPENAI_EMB_DIMENSIONS,
                query_language=AZURE_SEARCH_QUERY_LANGUAGE,
                query_speller=AZURE_SEARCH_QUERY_SPELLER,
            )

            current_app.config[CONFIG_CHAT_VISION_APPROACH] = ChatReadRetrieveReadVisionApproach(
                search_client=search_client,
                openai_client=openai_client,
                blob_container_client=blob_container_client,
                auth_helper=auth_helper,
                vision_endpoint=AZURE_VISION_ENDPOINT,
                vision_token_provider=token_provider,
                chatgpt_model=OPENAI_CHATGPT_MODEL,
                chatgpt_deployment=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                gpt4v_deployment=AZURE_OPENAI_GPT4V_DEPLOYMENT,
                gpt4v_model=AZURE_OPENAI_GPT4V_MODEL,
                embedding_model=OPENAI_EMB_MODEL,
                embedding_deployment=AZURE_OPENAI_EMB_DEPLOYMENT,
                embedding_dimensions=OPENAI_EMB_DIMENSIONS,
                query_language=AZURE_SEARCH_QUERY_LANGUAGE,
                query_speller=AZURE_SEARCH_QUERY_SPELLER,
            )

    @bp.after_app_serving
    async def close_clients():
        await current_app.config[CONFIG_SEARCH_CLIENT].close()
        await current_app.config[CONFIG_BLOB_CONTAINER_CLIENT].close()
        if current_app.config.get(CONFIG_USER_BLOB_CONTAINER_CLIENT):
            await current_app.config[CONFIG_USER_BLOB_CONTAINER_CLIENT].close()

    return bp