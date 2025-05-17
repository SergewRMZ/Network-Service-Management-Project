from flask import Blueprint, jsonify, request
from services.user_service import UserService
from config import ROUTERS
#  from configpractia import ROUTERS ?

user_service = UserService(ROUTERS)

users_bp = Blueprint('usuarios', __name__)

@users_bp.route("/", methods=["GET"])
def get_users():
    users = user_service.get_all_users()

    return jsonify(users), 200

@users_bp.route("/", methods=["POST"])
def create_users():

    body = request.get_json()

    new_user = {
        "username": body.get("username"),
        "password": body.get("password"),
        "privilege": body.get("privilege") 
    }

    result = user_service.create_user(new_user)

    return jsonify(result), 201

@users_bp.route("/", methods=["PUT"])
def update_users():

    body = request.get_json()

    new_user = {
        "username": body.get("username"),
        "password": body.get("password"),
        "privilege": body.get("privilege") 
    }

    result = user_service.update_users(
        body['old_username'],
        new_user
    )

    return jsonify(result), 200

@users_bp.route("/", methods=["DELETE"])
def delete_users():

    body = request.get_json()

    result = user_service.delete_user(body.get('username'))

    return jsonify(result), 200
