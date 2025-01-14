import logging
from functools import wraps
from typing import Any, Callable, Dict
from quart import abort, current_app, jsonify, request
from core.jwtauthentication import JWTManager
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

def handle_exceptions(route_fn):
    """
    Decorator that handles exceptions in asynchronous route functions.
    
    This decorator wraps the given asynchronous route function, catching and logging 
    any exceptions that occur during execution. It ensures that a consistent error 
    response is returned when an internal server error occurs.
    
    Args:
        f: The asynchronous route function to wrap.
    
    Returns:
        The wrapped asynchronous function that includes exception handling.
        
    Raises:
        500: If an unhandled exception occurs, the response will return a 
        JSON object with an "Internal Server Error" message.
    """
    @wraps(route_fn)
    async def decorated_function(*args, **kwargs):
        try:
            return await route_fn(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
    return decorated_function

def roles_required(roles):
    """
    Decorator that ensures the user has the required role(s) to access the route.
    
    This decorator wraps the given asynchronous route function and verifies that the 
    user has the required role(s) based on the decoded JWT. If the role is missing 
    or insufficient, a relevant error response is returned.
    
    Args:
        roles (list): A list of roles that are allowed to access the route.
    
    Returns:
        The wrapped asynchronous function with role-based access control.
    
    Raises:
        401: If the Authorization header is missing, invalid, or the JWT cannot be decoded.
        403: If the user’s role is not in the allowed roles.
    """
    def wrapper(fn):
        @wraps(fn)
        async def decorator(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"msg": "Missing or invalid Authorization header"}), 401
            
            token = auth_header.split(" ")[1]
            jwtmanager = JWTManager()
            decoded = jwtmanager.decode_jwt(token)
            if "msg" in decoded:  
                return jsonify(decoded), 401

            if decoded.get("role") not in roles:
                return jsonify({"msg": "Access denied: insufficient permissions"}), 403

            return await fn(*args, **kwargs)
        return decorator
    return wrapper

def authenticated_required(fn):
    """
    Decorator that ensures the user is authenticated to access the route.
    
    This decorator wraps the given asynchronous route function and verifies that the 
    request contains a valid JWT in the Authorization header. If the token is missing 
    or invalid, a relevant error response is returned.
    
    Args:
        fn: The asynchronous route function to wrap.
    
    Returns:
        The wrapped asynchronous function with authentication handling.
    
    Raises:
        401: If the Authorization header is missing, invalid, or the JWT cannot be decoded.
    """
    @wraps(fn)
    async def decorator(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"msg": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        jwtmanager = JWTManager()
        decoded = jwtmanager.decode_jwt(token)
        if "msg" in decoded:
            return jsonify(decoded), 401

        return await fn(*args, **kwargs)
    return decorator