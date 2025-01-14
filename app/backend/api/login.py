import base64
import json
import os
from quart import Blueprint, jsonify, request
from core.jwtauthentication import JWTManager

bp = Blueprint('login', __name__)

USERSENCODED = os.getenv("USERS", "")

decoded_bytes = base64.b64decode(USERSENCODED)
decoded_str = decoded_bytes.decode('utf-8')

USERS = json.loads(decoded_str)

@bp.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if user and user["password"] == password:
        jwtmanager = JWTManager()
        access_token = jwtmanager.generate_jwt(identity=username, role=user["role"])
        return jsonify({"access_token": access_token}), 200
    return jsonify({"msg": "Invalid credentials"}), 401
