from typing import Any, Dict
from quart import Blueprint, jsonify, make_response, request
from error import error_response
from utils.formatutils import format_as_ndjson
from decorators import authenticated, authenticated_required, handle_exceptions
from services.chatservice import ChatService

bp = Blueprint('chat', __name__)

@bp.route("/chat", methods=["POST"])
@authenticated
@handle_exceptions
async def chat(auth_claims: Dict[str, Any]):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    try:
        request_json = await request.get_json()
        chat_processor = ChatService(request_json=request_json, auth_claims=auth_claims)
        result = await chat_processor.process_chat_request()
        
        return jsonify(result)
    except Exception as error:
        return error_response(error, "/chat")    

@bp.route("/chat/stream", methods=["POST"])
@authenticated
@handle_exceptions
async def chat_stream(auth_claims: Dict[str, Any]):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    try:
        request_json = await request.get_json()
        chat_processor = ChatService(request_json=request_json, auth_claims=auth_claims)
        result = await chat_processor.process_chat_stream_request()
        
        # Formatting the response as NDJSON
        response = await make_response(format_as_ndjson(result))
        response.timeout = None  # type: ignore
        response.mimetype = "application/json-lines"
        return response
    except Exception as error:
        return error_response(error, "/chat")