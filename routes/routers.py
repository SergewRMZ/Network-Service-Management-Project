from flask import Blueprint, jsonify, request
from services.user_service import UserService
from services.routers_service import RouterService
from config import ROUTERS
import asyncio

user_service = UserService(ROUTERS)

router_service = RouterService(ROUTERS)

routers_bp = Blueprint('routers', __name__)

@routers_bp.route("/<host>/usuarios", methods=["GET"])
def get_users_by_router(host):
    users = user_service.get_users_by_router(host)
    if users is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404
    return jsonify(users), 200

@routers_bp.route("/<host>/usuarios", methods=["POST"])
def create_user_by_router(host):
    body = request.get_json()
    new_user = {
        "username": body.get("username"),
        "password": body.get("password"),
        "privilege": body.get("privilege", 1)
    }

    created = user_service.create_user_on_router(host, new_user)
    if created is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404
    return jsonify([created]), 201

@routers_bp.route("/<host>/usuarios", methods=["PUT"])
def update_user_by_router(host):
    body = request.get_json()
    new_user = {
        "username": body.get("username"),
        "password": body.get("password"),
        "privilege": body.get("privilege", 1)
    }

    updated = user_service.update_user_on_router(host, body.get("old_username"), new_user)
    if updated is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404
    return jsonify([updated]), 200

@routers_bp.route("/<host>/usuarios", methods=["DELETE"])
def delete_user_by_router(host):
    body = request.get_json()
    deleted = user_service.delete_user_on_router(host, body.get("username"))
    if deleted is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404
    return jsonify([deleted]), 200

@routers_bp.route("/", methods=["GET"])
def get_routers_snmp_info():
    info = asyncio.run(router_service.get_all_router_info())
    
    return jsonify(info), 200

@routers_bp.route("/<host>/", methods=["GET"])
def get_router_snmp_info(host):
    info = asyncio.run(router_service.get_router_info(host))

    if info is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404  
    
    return jsonify(info), 200

@routers_bp.route("/<host>/interfaces/", methods=["GET"])
def get_interface_info(host):
    info = asyncio.run(router_service.get_interface_info(host))

    if info is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404  
    
    return jsonify(info), 200