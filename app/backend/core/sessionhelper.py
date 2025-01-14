"""
Module for managing chat session identifiers in a chat application.

This module provides functionality to create unique session identifiers based on
whether chat history is enabled in the browser. It serves as a core utility for
maintaining conversation state across interactions.

Note: This is a core module and maintains strict backwards compatibility for
system-wide session management.
"""

import uuid
from typing import Union


def create_session_id(config_chat_history_browser_enabled: bool) -> Union[str, None]:
    """
    Creates a unique session identifier if chat history is enabled in the browser.

    This function generates UUIDs for tracking chat sessions when browser history
    is enabled, allowing for conversation persistence. When history is disabled,
    it returns None to indicate stateless operation.

    Args:
        config_chat_history_browser_enabled (bool): Flag indicating whether chat
            history is enabled in the browser configuration.

    Returns:
        Union[str, None]: A UUID string if chat history is enabled, None otherwise.
            The UUID is generated using version 4 (random) format.

    Example:
        When history is enabled:
            session_id = create_session_id(True)
            # Returns a UUID string like '550e8400-e29b-41d4-a716-446655440000'
        
        When history is disabled:
            session_id = create_session_id(False)
            # Returns None
    """
    if config_chat_history_browser_enabled:
        return str(uuid.uuid4())
    return None