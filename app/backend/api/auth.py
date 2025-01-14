from quart import Blueprint, current_app, jsonify
from config import CONFIG_AUTH_CLIENT

bp = Blueprint('auth', __name__)

# Send MSAL.js settings to the client UI
@bp.route("/auth_setup", methods=["GET"])
def auth_setup():
    auth_helper = current_app.config[CONFIG_AUTH_CLIENT]
    return jsonify(auth_helper.get_auth_setup_for_client())
