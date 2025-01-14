from typing import Any, Optional

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorQuery
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai_messages_token_helper import build_messages, get_token_limit

from approaches.approach import Approach, ThoughtStep
from core.authentication import AuthenticationHelper


class RetrieveThenReadApproach(Approach):
    """
    Implements a straightforward retrieve-then-read RAG approach that:
    1. First retrieves relevant documents from search using the raw user query
    2. Then uses OpenAI to generate a response based on the retrieved content
    
    This approach is optimized for direct question-answering without maintaining 
    conversation context, making it ideal for standalone HR/IT knowledge base queries.
    """

    # Base system prompt configuring the assistant's behavior
    system_chat_template = (
        "You are a knowledgeable paralegal/regulatory specialist helping Altalink users with their General Tariff Application (GTA) related queries. "
        + "Use 'you' to refer to the individual asking the questions even if they ask with 'I'. "
        + "Answer the following question using only the data provided in the sources below. "
        + "Each source has a name followed by colon and the actual information. Always include the source name for each fact you use in the response. "
        + "If you cannot answer using the sources below, say you don't know. Use the examples below to guide your answer."
    )

    # Example conversation showing expected question/answer format
    question = """
        'What renewable integration strategies were mentioned in the 2019 GTA filing?'

        Sources:
        GTA_2019.txt: The 2019 GTA filing discusses preliminary feasibility studies for integrating wind and solar resources into the distribution network.
        GTA_2020.txt: The 2020 GTA filing proposes a pilot program for large-scale solar integration.
        RenewableEnergyRegulations.pdf: Outlines compliance standards for integrating renewable sources.
    """
    answer = "The 2019 GTA filing mentions conducting preliminary feasibility studies for integrating wind and solar resources into the distribution network [GTA_2019.txt]."

    def __init__(
        self,
        *,
        search_client: SearchClient,
        auth_helper: AuthenticationHelper,
        openai_client: AsyncOpenAI,
        chatgpt_model: str,
        chatgpt_deployment: Optional[str],  # Not needed for non-Azure OpenAI
        embedding_model: str,
        embedding_deployment: Optional[str],  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embedding_dimensions: int,
        query_language: str,
        query_speller: str,
    ):
        """
        Initialize the retrieve-then-read approach with required clients and configuration.
        
        Args:
            search_client: Azure Cognitive Search client
            auth_helper: Helper for authentication and authorization
            openai_client: Azure OpenAI or OpenAI client
            chatgpt_model: Name of chat completion model
            chatgpt_deployment: Optional Azure deployment name
            embedding_model: Name of embedding model
            embedding_deployment: Optional Azure embedding deployment
            embedding_dimensions: Dimension of embedding vectors
            query_language: Language code for search queries
            query_speller: Spelling correction mode
        """
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.openai_client = openai_client
        self.auth_helper = auth_helper
        self.chatgpt_model = chatgpt_model
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.chatgpt_deployment = chatgpt_deployment
        self.embedding_deployment = embedding_deployment
        self.query_language = query_language
        self.query_speller = query_speller
        self.chatgpt_token_limit = get_token_limit(chatgpt_model, self.ALLOW_NON_GPT_MODELS)

    async def run(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """
        Executes the retrieve-then-read approach for a single question.
        
        Process:
        1. Takes last message as the query
        2. Performs search to retrieve relevant documents
        3. Generates response using retrieved sources
        
        Args:
            messages: List of conversation messages (uses only last message)
            session_state: Not used in this approach
            context: Additional parameters and overrides

        Returns:
            Dict containing response message and context information
        """
        # Extract query and configuration
        q = messages[-1]["content"]
        if not isinstance(q, str):
            raise ValueError("The most recent message content must be a string.")
        overrides = context.get("overrides", {})
        seed = overrides.get("seed", None)
        auth_claims = context.get("auth_claims", {})

        # Configure search parameters
        use_text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        use_vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_ranker = True if overrides.get("semantic_ranker") else False
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        top = overrides.get("top", 3)
        minimum_search_score = overrides.get("minimum_search_score", 0.0)
        minimum_reranker_score = overrides.get("minimum_reranker_score", 0.0)
        filter = self.build_filter(overrides, auth_claims)

        # Prepare vector query if needed
        vectors: list[VectorQuery] = []
        if use_vector_search:
            vectors.append(await self.compute_text_embedding(q))

        # Retrieve relevant documents
        results = await self.search(
            top,
            q,
            filter,
            vectors,
            use_text_search,
            use_vector_search,
            use_semantic_ranker,
            use_semantic_captions,
            minimum_search_score,
            minimum_reranker_score,
        )

        # Process search results
        sources_content = self.get_sources_content(results, use_semantic_captions, use_image_citation=False)
        content = "\n".join(sources_content)
        user_content = q + "\n" + f"Sources:\n {content}"

        # Generate response using retrieved sources
        response_token_limit = 1024
        updated_messages = build_messages(
            model=self.chatgpt_model,
            system_prompt=overrides.get("prompt_template", self.system_chat_template),
            few_shots=[{"role": "user", "content": self.question}, {"role": "assistant", "content": self.answer}],
            new_user_content=user_content,
            max_tokens=self.chatgpt_token_limit - response_token_limit,
            fallback_to_default=self.ALLOW_NON_GPT_MODELS,
        )

        chat_completion = await self.openai_client.chat.completions.create(
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            messages=updated_messages,
            temperature=overrides.get("temperature", 0.3),
            max_tokens=response_token_limit,
            n=1,
            seed=seed,
        )

        # Prepare response with metadata
        data_points = {"text": sources_content}
        extra_info = {
            "data_points": data_points,
            "thoughts": [
                ThoughtStep(
                    "Search using user query",
                    q,
                    {
                        "use_semantic_captions": use_semantic_captions,
                        "use_semantic_ranker": use_semantic_ranker,
                        "top": top,
                        "filter": filter,
                        "use_vector_search": use_vector_search,
                        "use_text_search": use_text_search,
                    },
                ),
                ThoughtStep(
                    "Search results",
                    [result.serialize_for_results() for result in results],
                ),
                ThoughtStep(
                    "Prompt to generate answer",
                    updated_messages,
                    (
                        {"model": self.chatgpt_model, "deployment": self.chatgpt_deployment}
                        if self.chatgpt_deployment
                        else {"model": self.chatgpt_model}
                    ),
                ),
            ],
        }

        return {
            "message": {
                "content": chat_completion.choices[0].message.content,
                "role": chat_completion.choices[0].message.role,
            },
            "context": extra_info,
            "session_state": session_state,
        }