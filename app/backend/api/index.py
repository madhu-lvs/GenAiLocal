from quart import Blueprint, current_app, jsonify
from decorators import roles_required
from config import CONFIG_INGESTER
from azure.core.exceptions import ResourceNotFoundError

bp = Blueprint('index', __name__)

@bp.post("/rebuild_index")
async def rebuild_index():
    try:
        ingester = current_app.config[CONFIG_INGESTER]
        await ingester.rerun_indexer(reset=True)
        return jsonify({"message": f"index rebuild initiated successfully"}), 200
    except ResourceNotFoundError as error:
        if error.status_code != 404:
            current_app.logger.exception("Error rebuilding index", error)

@bp.post("/rerun_index")
async def rerun_index():
    try:
        ingester = current_app.config[CONFIG_INGESTER]
        await ingester.rerun_indexer(reset=False)
        return jsonify({"message": f"index rerun initiated successfully"}), 200
    except Exception as error:
        if error.status_code != 404:
            current_app.logger.exception("Error Running Indexer", error)