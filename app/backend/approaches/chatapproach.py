import json
import re
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional

from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from approaches.approach import Approach

class ChatApproach(Approach, ABC):
    """
    Abstract base class implementing conversation handling for RAG-powered chat experiences.
    Extends the core Approach class with chat-specific functionality including conversation 
    history management, query generation, and follow-up question handling.
    """
    
    # Example conversations to help guide query generation for GTA scenarios
    query_prompt_few_shots: list[ChatCompletionMessageParam] = [
        # few-shot 1           
        {"role": "user", "content": "Summarize the applied-for revenue requirements in the last three GTA filings."},
        {"role": "assistant", "content": """
            AltaLink's applied-for revenue requirements for each General Tariff Application (GTA) period are as follows: 
                Year A to Year B GTA
                    - Year A: $RevenueA
                    - Year B: $RevenueB
                Year C to Year D GTA
                    - Year C: $RevenueC
                    - Year D: $RevenueD
                Year E to Year F GTA
                    - Year E: $RevenueE
                    - Year F: $RevenueF
            These revenue requirements reflect the projected cost of service, inclusive of operating expenses, capital investments, and rate of return allowances required to maintain and enhance AltaLink's transmission system. The figures are supported by evidence from the following exhibits:
            References: 
                - "2021 GTA Application Updated 20190821 Clean [23848-X0002.02].pdf"
                - "AML 2022-2023 GTA Application Updated Sep2021 Clean [26509-X0002.01].pdf"
                - "AML 2024-2025 GTA Amendment - Application Revised Clean [28174-X0006.01].pdf"
        """},
        # few-shot 2
        {"role": "user", "content": "Identify each Alberta utility that has proposed capitalizing cloud computing costs in the GTA submissions between Year A and Year B and summarize their proposals and reasons."},
        {"role": "assistant", "content": """
            The following Alberta utilities have proposed capitalizing cloud computing costs or addressed cloud-related expenditures in their General Tariff Applications (GTAs):
            EPCOR (EDTI): 
                - Proposal: EPCOR proposes to treat expenditures for cloud-based software as a service (SaaS) as "capital-like" costs, recovering them over a 10-year period instead of expensing them immediately.
                - Rationale:
                    - Intergenerational Equity: Distributes costs over the service life to ensure that future and current ratepayers share the costs equitably.
                    - Parity with On-Premise Solutions: Aligns cost treatment of cloud-based software with traditional on-premise IT investments.
                    - Risk Mitigation: Enables prospective true-ups to ensure fair cost recovery if actual expenditures deviate from forecasts.
            ENMAX
                - Proposal: While not explicitly proposing capitalization, ENMAX introduces an "IT allocator" model to allocate cloud-related costs more fairly.
                - Rationale:
                    - Modernization of Cost Allocation: Shifts allocation logic from device-based to application-based models, which better reflects modern IT service models.
                    - Cost Fairness: Aligns IT costs with usage patterns, ensuring fair treatment of cloud-related expenditures.
            AltaLink and ATCO
                - Neither AltaLink nor ATCO proposed to capitalize cloud computing costs. Both utilities continue to treat such costs as operating expenses under existing accounting practices.
            References:
                - "AML 2024-2025 GTA Amendment - Application Revised Clean [28174-X0006.01].pdf"
                - "AET 2023-2025 General Tariff Application Revised 2 [27062-X0014.02].pdf"
                - "EPC 2023-2025 General Tariff Application [27581-X0016].pdf"
        """},
        # few-shot 3
        {"role": "user", "content": "What are the details of AltaLink's third-party liability insurance costs from the Year A to Year B GTA?"},
        {"role": "assistant", "content": """
            AltaLink's third-party liability insurance costs for the Year A to Year B period are as follows:
                - Coverage Limit: $400 million for both Year A and Year B.
                - Premium Forecasts:
                    - Year A: $LimitForecastA
                    - Year B: $LimitForecastB
                - Deductible: The deductible increased from $ValueA in Year A to $ValueB in Year B, resulting in a premium reduction of approximately $SavingsValue (X%).
                - Purpose of Coverage: Protects ratepayers from the financial impact of catastrophic losses, such as wildfire damage caused by AltaLink's infrastructure.
            References:
                - "Appendix 03 (Insurance) [28174-X0010].pdf"
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 4
        {"role": "user", "content": "Compare and contrast the self-insurance policies in all AltaLink GTAs."},
        {"role": "assistant", "content": """
            AltaLink's Self-Insurance Reserve (SIR) policies have remained consistent across the Year A to Year B, Year C to Year D, and Year E to Year F General Tariff Application (GTA) periods. Key components are as follows:
                - Year A to Year B GTA
                    - Scope of Coverage: Property damage, executive risk (Directors & Officers), and non-owned aircraft claims.
                    - Eligibility: Sudden, accidental, and uncontrollable events with a loss threshold exceeding $100,000.
                    - True-Up Mechanism: Target balance of $0 with a tolerance range of +/- 0.5M. Adjustments are made in the next GTA if the balance exceeds this range.
                - Year C to Year D GTA: No material changes from Year C to Year D policies.
                - Year E to Year F GTA: No material changes from previous periods.
            References:
                - "Appendix 03 (Insurance) [28174-X0010].pdf"
                - "AML 2022-2023 GTA - Appendix 03 (Insurance) [26509-X0006].pdf"
                - "AML 2019-2021 GTA - Appendix 03 (Insurance) [23848-X0006].pdf"
        """},
        # few-shot 5
        {"role": "user", "content": "List the specific information requests related to wildfire in the Year A to Year B GTA."},
        {"role": "assistant", "content": """
            The following information requests (IRs) pertain to wildfire-related topics in the Year A to Year B General Tariff Application (GTA):
                - "AML-AFREA-2023OCT10-016.pdf"
                - "AML-AFREA-2023OCT10-018.pdf"
                - "AML-AUC-2023OCT04-012.pdf"
                - "AML-AUC-2023OCT04-077.pdf"
                - "AML-AUC-2023OCT04-078.pdf"
                - "AML-AUC-2023OCT04-079.pdf"
                - "AML-AUC-2023OCT04-081.pdf"
                - "AML-AUC-2023OCT04-083.pdf"
                - "AML-AUC-2023OCT04-084.pdf"
                - "AML-AUC-2023OCT04-086.pdf"
                - "AML-AUC-2023OCT04-087.pdf"
                - "AML-AUC-2023OCT04-088.pdf"
                - "AML-AUC-2023OCT04-089.pdf"
                - "AML-AUC-2023OCT04-093.pdf"
                - "AML-AUC-2023OCT04-095.pdf"
                - "AML-CCA-2023OCT10-001.pdf"
                - "AML-CCA-2023OCT10-002.pdf"
                - "AML-CCA-2023OCT10-016.pdf"
                - "AML-IPCAA-2023OCT10-003.pdf"
                - "AML-IPCAA-2023OCT10-013.pdf"
                - "AML-UCA-2023OCT10-010.pdf"
                - "AML-UCA-2023OCT10-011.pdf"
                - "AML-UCA-2023OCT10-012.pdf"
                - "AML-UCA-2023OCT10-013.pdf"
                - "AML-UCA-2023OCT10-014.pdf"
                - "AML-UCA-2023OCT10-015.pdf"
                - "AML-UCA-2023OCT10-016.pdf"
                - "AML-UCA-2023OCT10-017.pdf"
            These IRs focus on wildfire mitigation strategies, deferral accounts, cost allocation, and risk assessment.
        """},
        # few-shot 6
        {"role": "user", "content": "Summarize the interveners' requests regarding Appendix 13-D (Inventory) for the Year A to Year B GTA."},
        {"role": "assistant", "content": """
            The interveners' requests related to Appendix 13-D (Inventory) in the Year A to Year B General Tariff Application (GTA) are summarized as follows:
            - Accounting Practices and Asset Classification:
                - Clarification of AltaLink's accounting treatment for misclassified assets identified in 2023.
                - Request for an explanation of how the term "rotational equipment" differs from "non-rotational equipment" and how this impacts cost classification.
            - Ratepayer Impact Analysis:
                - Justification of AltaLink's decision not to apply historical corrections for prior asset classification errors.
                - Requests for a quantification of the financial impact of this misclassification on revenue requirements.
            - Depreciation and Rate Calculations:
                - Comparative analysis of depreciation calculations for "misclassified" versus "correctly classified" assets.
            - Procurement and Risk Mitigation:
                - Requests for a rationale for transformer procurement strategies, particularly the justification for advance purchases of emergency spares.
                - Request for details on AltaLink's probabilistic model for inventory planning, including the 95% confidence threshold.
            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 7
        {"role": "user", "content": "What was the dollar value of the reduction to building operating expenses in Year A from the most recent GTA?"},
        {"role": "assistant", "content": """
            The reduction to building operating expenses for Year A, as reflected in AltaLink's Year A to Year B General Tariff Application (GTA), was approximately $0.4 million. This reduction is part of a broader effort to manage operational efficiencies and cost containment.
            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 8
        {"role": "user", "content": "Are STIP, LTIP, and benefit amounts included in the ES&G account?"},
        {"role": "assistant", "content": """
            Yes, STIP (Short-Term Incentive Plan), LTIP (Long-Term Incentive Plan), and benefit amounts are included in the ES&G (Employee Salaries & General) account. AltaLink's filing confirms that compensation amounts, including STIP and LTIP, are applied consistently across both capital projects and operational expenditures. These amounts are standardized to avoid monthly fluctuations and are applied as part of the broader strategy for equitable treatment of internal labor costs.
            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 9
        {"role": "user", "content": "What is the primary purpose of the wildfire mitigation program from AltaLink's most recent GTA?"},
        {"role": "assistant", "content": """
            The primary purpose of AltaLink's Wildfire Mitigation Program (WMP), as outlined in the last General Tariff Application (GTA), is to reduce the risk of wildfires caused by transmission infrastructure. The program includes a combination of capital investments and operational adjustments, such as:
            - Capital Projects: Upgrades to transmission infrastructure, including the use of non-combustible materials and enhanced system hardening.
            - Vegetation Management: Implementation of advanced vegetation clearing techniques around transmission lines to reduce ignition risk.
            - Risk Assessment and Monitoring: Deployment of predictive risk modeling and monitoring systems to identify and mitigate high-risk zones in real time.
            These measures aim to protect Alberta's natural environment, reduce the risk of fire-related damage to utility assets, and safeguard public safety.         
            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 10
        {"role": "user", "content": "What did the Consumers' Coalition of Alberta (CCA) say about credit rating reports in the most recent GTA proceeding?"},
        {"role": "assistant", "content": """
            The Consumers' Coalition of Alberta (CCA) provided the following feedback and requests regarding credit rating reports in AltaLink's Year A General Tariff Application (GTA):
            - Requests for Information:
                - Detailed notes and communications AltaLink shared with credit rating agencies.
                - Copies of presentations given to rating agencies that referenced wildfire risk.
            - Concerns:
                - Suggested that AltaLink's application may overstate wildfire risk to justify cost recovery.
                - Raised concerns regarding the alignment of shareholder interests with customer interests.
            - Ratepayer Impact:
                - Expressed concern that perceptions from rating agencies could increase borrowing costs for AltaLink, which may be passed on to ratepayers.
                - Requested analysis on the cost impact of potential credit downgrades (1-notch, 2-notch, and "junk" scenarios).
            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
                - "CCA Evidence of Dustin Madsen [28174-X0422].pdf"
        """},
        # few-shot 11
        {"role": "user", "content": "What are the definitions of salvage in the context of utility regulation?"},
        {"role": "assistant", "content": """
            In the context of utility regulations, salvage cost means the total cost of removing an asset from service. This term is synonymous with the term “Cost of Removal” as detailed in the Uniform System of Accounts (USA) Document, approved in EUB Bulletin 2006-025. The USA defines Cost of Removal as the total cost of demolishing, dismantling, tearing down or otherwise removing assets from service, including the cost of transportation and handling incidental thereto.
            - Salvage expenditure means salvage cost.
            - Standard salvage percentage means the allocation percentage applied to each project type established in the 2013-2014 Cost of Salvage Study.
            - Standard salvage costs means the salvage costs which result from applying the standard salvage percentages.
            - Standard salvage expenditures means standard salvage costs.
            References:
                - "Appendix 18 (Capital Supplemental Info) [28174-X0049].pdf"
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
        """},
        # few-shot 12
        {"role": "user", "content": "What were the Commission's directions for the Year A to Year B test period?"},
        {"role": "assistant", "content": """
            The Commission's directions for AltaLink during the Year A to Year B General Tariff Application (GTA) test period are as follows:
            - Labor Compensation Adjustments:
                - Reduce unionized employee base pay increases to 1.8% and reflect this change in the compliance filing.
                - Apply a 1.8% increase for non-union and executive base pay for Year A and Year B, reflecting these changes in the revenue requirement.
            - Operational Efficiency Directives:
                - Implement a 10% reduction in forecasted Operations & Maintenance (O&M) expenditures for Year A and Year B.
                - Prohibit any reclassification of O&M to capital expenditures to avoid offsetting reductions.
            - IT Expenditure Revisions:
                - Adjust IT capital forecasts in response to findings on capital program efficiency.
                - Provide comparative IT expenditures (O&M and capital) with industry benchmarks in future GTAs.
            - Other Compliance Requirements:
                - Reconcile emergency spare inventory and submit a list of all capitalized emergency spare assets with supporting rationale.
                - Remove specific forecasted capital expenditures related to substation and station service projects in Year A and Year B.
                - Provide analysis and support for battery bank replacements, SCADA program costs, and wildlife mitigation project costs.
            References:
                - "Decision 26509-D01-2022 Corrigenda (AML KLP PLP 2022-2023 GTAs and 2020 DACDA).pdf"
        """},
        # few-shot 13
        {"role": "user", "content": """What were the forecast and actual capital expenditures for the “Smart Key Implementation Project” business case from the Year C to Year D GTA?"""},
        {"role": "assistant", "content": """
            | Year (Filing) | Forecast ($M) | Actual ($M) | 
            |--------|----------|---------| 
            | Year A |  $ForecastA  |  $ActualA  | 
            | Year B |  $ForecastB  |  $ActualB  | 
            References: 
                - "AML 2022-2023 GTA - Appendix 13-B (Information Services) [26509-X0033].pdf"
                - "Appendix 13-B (Information Services) [28174-X0039].pdf"
        """},
        # few-shot 14
        {"role": "user", "content": "What did the interveners say about hearing costs in the Year A to Year B GTA proceeding?"},
        {"role": "assistant", "content": """
            In IR AML-IPCAA-2023OCT10-004, IPCAA requested clarity on the substantial reduction in hearing costs and whether the reduction could lead to expected future efficiencies. IPCAA also requested clarity on the rationale for a Hearing Support FTE role in the Law & Regulatory department with the substantial reduction in hearings. 
            References:
                - "AML IR Responses to IPCAA (RequestID) [DocumentID].pdf"        
        """},
        # few-shot 15
        {"role": "user", "content": "Did Enmax request any funding for EAM systems between Year A and Year B?"},
        {"role": "assistant", "content": """
            Enmax did not request any funding for their EAMS initiative for the Year A to Year B test period.
            References:
                - "EPC 2023-2025 General Tariff Application [27581-X0016].pdf"        
        """},
        # few-shot 16
        {"role": "user", "content": "When and under what conditions can vegetation management cost be capitalized?"},
        {"role": "assistant", "content": """
            The determination for the capitalization of Vegetation Management costs is dependent on the nature of the expenses. Initial clearing, both mechanical and chemical, are to be capitalized to appropriate plant accounts which they directly benefited. This may include structures and improvement account 352 for Transmission related assets. 
         
            Subsequent costs are expensed to Operation and Maintenance of vegetation management account 571.1. as outlined by the AUC in Bulletin 2006-25 issued May 8, 2006. This accounting treatment is demonstrated in ATCO Electric Transmission (AET) 2023-25 GTA.

            References:
                - "AET 2023-2025 General Tariff Application Revised 2 [27062-X0014.02].pdf"
                - "2-1 to 2-22 - TCM Business Cases [27062-X0196].pdf"        
        """},
        # few-shot 17
        {"role": "user", "content": "What were the salary increases for field staff in Year A through Year C?"},
        {"role": "assistant", "content": """
            The available information regarding field staff salary increases is as follows:
            - Year A: 2.1% increase
            - Year B: Data not found in the knowledge base
            - Year C: 1.8% increase

            Note that while increases for Years A and C are documented in the salary and wage schedules, information for Year B is not present in the available materials. A complete analysis would require additional documentation for Year B.

            References:
                - "AML IR Response to AUC (RequestID) [DocumentID].pdf"
                - "2024-2025 GTA Amendment - Application Revised Clean [28174-X0006.01].pdf"
        """},      
    ]

    # Constant indicating no relevant search results found
    NO_RESPONSE = "0"

    # Prompt to generate contextually relevant follow-up questions
    follow_up_questions_prompt_content = """Generate 3 very brief follow-up questions that the user would likely ask next.
    Enclose the follow-up questions in double angle brackets. Example:
    <<What regulatory adjustments influenced the 2021 GTA approvals?>>
    <<How did customer consumption patterns shift from 2019 to 2020?>>
    <<Are there any documented appeals or challenges to the 2020 GTA decisions?>> 
    Do not repeat questions that have already been asked.
    Make sure the last question ends with ">>".
    """

    # Template for converting chat context into effective search queries
    query_prompt_template = query_prompt_template = """
    You are a knowledgeable paralegal/regulatory specialist supporting AltaLink's General Tariff Application (GTA) processes. Your purpose is to provide comprehensive answers while staying focused on the specific ask.

    You are capable of:
    - Answering GTA-related questions
    - Finding relevant citations and precedents
    - Identifying similar historical examples
    - Suggesting appropriate phrasing based on successful filings
    - Providing relevant information for IR responses
    - Identifying inconsistencies within filings
    - Comparing filing content across multiple years
    - Comparing filing content across different utilities
    - Combining multi-year and/or multi-utility comparisons as needed
    
    Key Guidelines:
    - Focus on addressing the specific ask in each interaction
    - Provide comprehensive responses that fully address the question, while staying focused on the specific ask
    - Ask for clarification if the request is unclear
    - Never speculate; if information isn't in the knowledge base, state that it cannot be found and invite the user to clarify or provide more details
    - If multiple authoritative sources present conflicting information, present both versions objectively, summarize the differences, and encourage the user to determine which interpretation best fits their scenario
    - Maintain professional but clear language
    
    Technical Requirements:
    - Do not include source filenames, document names, or file extensions in responses
    - Avoid ALL special characters including [], >>, <<, +, **, and file extensions like .pdf
    - Present information in natural language without automatic numbering or bullet points
    - Let the system handle the technical aspects of citations and source chunks
    
    [Conversation history and the user's latest question will be appended here at runtime]

    Remember: Focus on providing the most relevant and helpful response to the current question while maintaining accuracy and professionalism.
    """

    @property
    @abstractmethod
    def system_message_chat_conversation(self) -> str:
        """
        Abstract property that defines the base system message for the chat conversation.
        Should be implemented by concrete classes to define the assistant's persona and behavior.
        """
        pass

    @abstractmethod
    async def run_until_final_call(self, messages, overrides, auth_claims, should_stream) -> tuple:
        """
        Abstract method that implements the core chat processing logic.
        Should be implemented by concrete classes to define how messages are processed.

        Args:
            messages: List of chat messages in the conversation
            overrides: Dictionary of processing overrides
            auth_claims: Authentication claims for the user
            should_stream: Boolean indicating if responses should be streamed

        Returns:
            Tuple containing conversation extra info and the chat completion coroutine
        """
        pass

    def get_system_prompt(self, override_prompt: Optional[str], follow_up_questions_prompt: str) -> str:
        """
        Constructs the final system prompt by combining the base prompt with any overrides.
        
        Args:
            override_prompt: Optional custom prompt to override default
            follow_up_questions_prompt: Prompt for generating follow-up questions

        Returns:
            Complete system prompt with injected context
        """
        if override_prompt is None:
            return self.system_message_chat_conversation.format(
                injected_prompt="", follow_up_questions_prompt=follow_up_questions_prompt
            )
        elif override_prompt.startswith(">>>"):
            return self.system_message_chat_conversation.format(
                injected_prompt=override_prompt[3:] + "\n", follow_up_questions_prompt=follow_up_questions_prompt
            )
        else:
            return override_prompt.format(follow_up_questions_prompt=follow_up_questions_prompt)

    def get_search_query(self, chat_completion: ChatCompletion, user_query: str):
        """
        Extracts the search query from a chat completion response.
        Handles both tool-based and direct response formats.

        Args:
            chat_completion: The ChatCompletion response
            user_query: Original user query as fallback

        Returns:
            Extracted search query string
        """
        response_message = chat_completion.choices[0].message

        if response_message.tool_calls:
            for tool in response_message.tool_calls:
                if tool.type != "function":
                    continue
                function = tool.function
                if function.name == "search_sources":
                    arg = json.loads(function.arguments)
                    search_query = arg.get("search_query", self.NO_RESPONSE)
                    if search_query != self.NO_RESPONSE:
                        return search_query
        elif query_text := response_message.content:
            if query_text.strip() != self.NO_RESPONSE:
                return query_text
        return user_query

    def extract_followup_questions(self, content: Optional[str]):
        """
        Extracts suggested follow-up questions from the response content.
        Questions should be enclosed in double angle brackets <<>>.

        Args:
            content: Response content containing follow-up questions

        Returns:
            Tuple of (cleaned content, list of follow-up questions)
        """
        if content is None:
            return content, []
        return content.split("<<")[0], re.findall(r"<<([^>>]+)>>", content)

    async def run_without_streaming(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        session_state: Any = None,
    ) -> dict[str, Any]:
        """
        Processes a chat interaction without streaming the response.
        
        Args:
            messages: List of conversation messages
            overrides: Processing override parameters
            auth_claims: User authentication claims
            session_state: Optional session state to maintain

        Returns:
            Dict containing response message, context and session state
        """
        extra_info, chat_coroutine = await self.run_until_final_call(
            messages, overrides, auth_claims, should_stream=False
        )
        chat_completion_response: ChatCompletion = await chat_coroutine
        content = chat_completion_response.choices[0].message.content
        role = chat_completion_response.choices[0].message.role
        if overrides.get("suggest_followup_questions"):
            content, followup_questions = self.extract_followup_questions(content)
            extra_info["followup_questions"] = followup_questions
        chat_app_response = {
            "message": {"content": content, "role": role},
            "context": extra_info,
            "session_state": session_state,
        }
        return chat_app_response

    async def run_with_streaming(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        session_state: Any = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Processes a chat interaction with streaming responses.
        
        Args:
            messages: List of conversation messages
            overrides: Processing override parameters
            auth_claims: User authentication claims 
            session_state: Optional session state to maintain

        Yields:
            Dict chunks containing streamed response content
        """
        extra_info, chat_coroutine = await self.run_until_final_call(
            messages, overrides, auth_claims, should_stream=True
        )
        yield {"delta": {"role": "assistant"}, "context": extra_info, "session_state": session_state}

        followup_questions_started = False
        followup_content = ""
        async for event_chunk in await chat_coroutine:
            event = event_chunk.model_dump()
            if event["choices"]:
                completion = {
                    "delta": {
                        "content": event["choices"][0]["delta"].get("content"),
                        "role": event["choices"][0]["delta"]["role"],
                    }
                }
                content = completion["delta"].get("content")
                content = content or ""
                if overrides.get("suggest_followup_questions") and "<<" in content:
                    followup_questions_started = True
                    earlier_content = content[: content.index("<<")]
                    if earlier_content:
                        completion["delta"]["content"] = earlier_content
                        yield completion
                    followup_content += content[content.index("<<") :]
                elif followup_questions_started:
                    followup_content += content
                else:
                    yield completion
        if followup_content:
            _, followup_questions = self.extract_followup_questions(followup_content)
            yield {"delta": {"role": "assistant"}, "context": {"followup_questions": followup_questions}}

    async def run(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """
        Main entry point for non-streaming chat processing.
        Extracts context and processes the conversation.

        Args:
            messages: List of conversation messages
            session_state: Optional session state
            context: Additional context parameters

        Returns:
            Dict containing response message and context
        """
        overrides = context.get("overrides", {})
        auth_claims = context.get("auth_claims", {})
        return await self.run_without_streaming(messages, overrides, auth_claims, session_state)

    async def run_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Main entry point for streaming chat processing.
        Extracts context and processes the conversation with streaming.

        Args:
            messages: List of conversation messages
            session_state: Optional session state
            context: Additional context parameters

        Yields:
            Dict chunks containing streamed response
        """
        overrides = context.get("overrides", {})
        auth_claims = context.get("auth_claims", {})
        return self.run_with_streaming(messages, overrides, auth_claims, session_state)