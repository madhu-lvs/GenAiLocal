import logging

from openai import APIError
from quart import jsonify

# Standard error message template for application errors
ERROR_MESSAGE = """The app encountered an error processing your request.
If you are an administrator of the app, view the full error in the logs. See aka.ms/appservice-logs for more information.
Error type: {error_type}
"""

# Specific error message for content filtering violations
ERROR_MESSAGE_FILTER = """Your message contains content that was flagged by the OpenAI content filter."""

# Specific error message for token length limit violations
ERROR_MESSAGE_LENGTH = """Your message exceeded the context length limit for this OpenAI model. Please shorten your message or change your settings to retrieve fewer search results."""


def error_dict(error: Exception) -> dict:
    """
    Converts an exception into a standardized error response dictionary.
    
    This function handles specific OpenAI API errors with custom messages and
    provides a generic error message for other types of exceptions.
    
    Args:
        error (Exception): The exception to convert into an error response
        
    Returns:
        dict: A dictionary containing the appropriate error message
        
    Examples:
        >>> try:
        ...     raise ValueError("Some error")
        ... except Exception as e:
        ...     response = error_dict(e)
        >>> response
        {'error': 'The app encountered an error...Error type: <class 'ValueError'>'}
    """
    if isinstance(error, APIError) and error.code == "content_filter":
        return {"error": ERROR_MESSAGE_FILTER}
    if isinstance(error, APIError) and error.code == "context_length_exceeded":
        return {"error": ERROR_MESSAGE_LENGTH}
    return {"error": ERROR_MESSAGE.format(error_type=type(error))}


def error_response(error: Exception, route: str, status_code: int = 500):
    """
    Creates a standardized JSON error response with appropriate status code and logging.
    
    This function handles the full error response flow:
    1. Logs the error with full stack trace
    2. Generates an appropriate error message
    3. Returns a JSON response with the correct status code
    
    Args:
        error (Exception): The exception to convert into an error response
        route (str): The route where the error occurred (for logging purposes)
        status_code (int, optional): HTTP status code to return. Defaults to 500.
            Will be overridden to 400 for content filter violations.
    
    Returns:
        tuple: A tuple containing (JSON response, status code) suitable for returning
        from a route handler
        
    Example:
        @app.route("/api/endpoint")
        async def my_route():
            try:
                # ... some code that might raise an exception
                pass
            except Exception as e:
                return error_response(e, "/api/endpoint")
    
    Note:
        Content filter violations always return status code 400 regardless of
        the status_code parameter, as they represent client errors rather than
        server errors.
    """
    logging.exception("Exception in %s: %s", route, error)
    if isinstance(error, APIError) and error.code == "content_filter":
        status_code = 400
    return jsonify(error_dict(error)), status_code