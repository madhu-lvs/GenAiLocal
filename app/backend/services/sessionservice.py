from typing import Any, Dict
from core.sessionhelper import create_session_id

class SessionService:
    def __init__(self, request_json: Dict[str, Any], chat_history_enabled: bool):
        """
        Initializes the SessionService with request data and chat history settings.
        
        Args:
            request_json (Dict[str, Any]): JSON request containing session-related data.
            chat_history_enabled (bool): Flag indicating if chat history is enabled.

        The constructor sets up the request data and determines whether chat history 
        is enabled for session management purposes.
        """
        self.request_json = request_json
        self.chat_history_enabled = chat_history_enabled
        self.session_state = None

    def get_session_state(self) -> str:
        """
        Retrieves the session state from the request or generates a new session ID.

        This method checks if a session state is provided in the incoming request. If 
        no session state is present, it generates a new session ID using the 
        `create_session_id` function, factoring in whether chat history is enabled.
        
        Returns:
            str: The current session state or a newly generated session ID.
        """
        self.session_state = self.request_json.get("session_state")
        if self.session_state is None:
            self.session_state = create_session_id(self.chat_history_enabled)
        return self.session_state
