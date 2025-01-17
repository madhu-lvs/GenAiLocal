from typing import cast
from quart import Blueprint, current_app, jsonify, request
from decorators import authenticated_required
from config import CONFIG_CHAT_APPROACH
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach


bp = Blueprint('lookup', __name__)

@bp.post("/lookup")
async def document_lookup():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    query = request_json.get("query", "")
    if query == "":
        return jsonify({"error": "request query key must not be an empty string"}), 415
    approach = cast(ChatReadRetrieveReadApproach, current_app.config[CONFIG_CHAT_APPROACH])
    list_of_documents = await approach.lookup_documents(query, {})
    return list_of_documents