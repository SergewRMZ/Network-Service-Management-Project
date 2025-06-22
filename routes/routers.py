from flask import Blueprint, jsonify, request
from services.user_service import UserService
from services.routers_service import RouterService
from services.monitor_service import MonitorService
from config import ROUTERS
import asyncio
import os
import json
user_service = UserService(ROUTERS)

router_service = RouterService(ROUTERS)
monitor_service = MonitorService(ROUTERS)

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

@routers_bp.route("/<host>", methods=["GET"])
def get_router_snmp_info(host):
    info = asyncio.run(router_service.get_router_info(host))

    if info is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404  
    
    return jsonify(info), 200

@routers_bp.route("/<host>/interfaces", methods=["GET"])
def get_interface_info(host):
    info = asyncio.run(router_service.get_interface_info(host))

    if info is None:
        return jsonify({"error": f"Router {host} no encontrado"}), 404  
    
    return jsonify(info), 200

# Rutas para MonitorService
@routers_bp.route("/<host>/interfaces/<path:interfaz>/octetos/<int:tiempo>", methods=["POST"])
def iniciar_monitoreo_octetos(host, interfaz, tiempo):
    duracion = request.args.get("duracion", default=60, type=int)
    ok = monitor_service.start_monitoring(host, interfaz, tiempo, duracion)
    if ok:
        return jsonify({
            "message": f"Monitoreo iniciado en {interfaz} del router {host}",
            "intervalo": tiempo,
            "duracion": duracion,
            "estado": "activo"
        }), 200
    else:
        return jsonify({
            "message": f"Ya hay un monitoreo activo en {interfaz} del router {host}",
            "estado": "en conflicto"
        }), 400

@routers_bp.route("/<host>/interfaces/<path:interfaz>/octetos", methods=["GET"])
def obtener_datos_monitoreo_octetos(host, interfaz):
    filename = f"data/{host.replace('.', '_')}_{interfaz.replace('/', '_')}.json"

    if not os.path.exists(filename):
        return jsonify({"error": "No hay datos almacenados para esta interfaz"}), 404

    with open(filename, "r") as f:
        data = json.load(f)

    return jsonify(data), 200
