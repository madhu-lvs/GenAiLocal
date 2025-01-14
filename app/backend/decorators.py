import logging
from functools import wraps
from typing import Any, Callable, Dict

from quart import abort, current_app, request

from config import CONFIG_AUTH_CLIENT, CONFIG_SEARCH_CLIENT
from core.authentication import AuthError
from error import error_response


def authenticated_path(route_fn: Callable[[str, Dict[str, Any]], Any]):
    """
    Decorator that enforces authentication and authorization for routes that access specific files or paths.
    
    This decorator performs the following security checks:
    1. Validates the authentication token if authentication is enabled
    2. Verifies the user has permission to access the requested path
    3. Handles authorization errors appropriately
    
    Args:
        route_fn: The route function to wrap. Should accept a path string and auth claims dictionary.
    
    Returns:
        The wrapped route function that includes authentication checks
        
    Raises:
        403: If authentication fails or user lacks permission to access the path
        500: If there's an unexpected error during authorization
    """
    @wraps(route_fn)
    async def auth_handler(path=""):
        auth_helper = current_app.config[CONFIG_AUTH_CLIENT]
        search_client = current_app.config[CONFIG_SEARCH_CLIENT]
        authorized = False

        try:
            auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
            authorized = await auth_helper.check_path_auth(path, auth_claims, search_client)
        except AuthError:
            abort(403)
        except Exception as error:
            logging.exception("Problem checking path auth %s", error)
            return error_response(error, route="/content")

        if not authorized:
            abort(403)

        return await route_fn(path, auth_claims)

    return auth_handler


def authenticated(route_fn: Callable[[Dict[str, Any]], Any]):
    """
    Decorator that enforces authentication for protected routes.
    
    This decorator extracts and validates authentication claims from request headers.
    It handles both enabled and disabled authentication scenarios based on application
    configuration.
    
    Args:
        route_fn: The route function to wrap. Should accept an auth claims dictionary.
    
    Returns:
        The wrapped route function that includes authentication handling
        
    Raises:
        403: If authentication fails or is invalid
    """
    @wraps(route_fn)
    async def auth_handler():
        auth_helper = current_app.config[CONFIG_AUTH_CLIENT]
        try:
            auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
        except AuthError:
            abort(403)

        return await route_fn(auth_claims)

    return auth_handler