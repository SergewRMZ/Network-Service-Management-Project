from flask import Blueprint, jsonify, request, send_file
from matplotlib import pyplot as plt
from config import ROUTERS

from services.user_service import UserService
from services.routers_service import RouterService
from services.monitor_service import MonitorService
from services.traps_service import TrapsService
import asyncio
import os
import json
import io

user_service = UserService(ROUTERS)
router_service = RouterService(ROUTERS)
monitor_service = MonitorService(ROUTERS)
traps_service = TrapsService(ROUTERS)

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
    duracion = request.args.get("duration", default=60, type=int)
    print("duracion obtenida:", duracion)
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

@routers_bp.route("/<host>/interfaces/<path:interfaz>/octetos", methods=["DELETE"])
def detener_monitoreo_octetos(host, interfaz):
    ok = monitor_service.stop_monitoring(host, interfaz)

    filename = f"data/{host.replace('.', '_')}_{interfaz.replace('/', '_')}.json"

    if ok:
        return jsonify({
            "message": f"Monitoreo detenido en {interfaz} del router {host}",
            "estado": "detenido",
            "archivo_guardado": os.path.exists(filename)
        }), 200
    else:
        return jsonify({
            "message": f"No había un monitoreo activo en {interfaz} del router {host}",
            "estado": "inexistente"
        }), 400

@routers_bp.route("/<host>/interfaces/<path:interfaz>/grafica", methods=["GET"])
def obtener_grafica_monitoreo(host, interfaz):
    filename = f"data/{host.replace('.', '_')}_{interfaz.replace('/', '_')}.json"
    if not os.path.exists(filename):
        return jsonify({"error": "No hay datos monitoreados para graficar"}), 404

    with open(filename, "r") as f:
        data = json.load(f)

    if not data:
        return jsonify({"error": "El archivo existe pero no contiene datos"}), 400

    # Extrae datos
    tiempos = [entry["timestamp"] for entry in data]
    octetos = [entry["octetos"] for entry in data]

    # Genera gráfica
    plt.figure(figsize=(10, 6))
    plt.plot(tiempos, octetos, marker='o', linestyle='-')
    plt.xticks(rotation=45)
    plt.title(f"Monitoreo de Octetos en {interfaz} ({host})")
    plt.xlabel("Tiempo")
    plt.ylabel("Octetos")
    plt.tight_layout()

    # Guarda en buffer en memoria
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return send_file(img, mimetype="image/png")

# Traps
# Get - json con estado de la interfaz
@routers_bp.route("/<host>/interfaces/<path:interfaz>/estado", methods=["GET"])
def estado_interfaz(host, interfaz):
    estado = traps_service.get_interface_trap_status(host, interfaz)
    if estado is None:
        return jsonify({"Error": f"No se encontro el router {host} o la interfaz {interfaz}"}), 404
    return jsonify(estado), 200


# Post - activa la captura de traps linkup y linkdown de una interfaz en espacifico, retornar json con el estado de la interfaz
@routers_bp.route("/<host>/interfaces/<path:interfaz>/estado", methods=["POST"])
def activar_traps_interfaz(host, interfaz):
    ok = traps_service.start_trap_capture(host, interfaz)
    if ok:
        estado = traps_service.get_interface_trap_status(host, interfaz)
        return jsonify({
            "message": f"Captura de traps activada para {interfaz} en {host}",
            "estado": estado
        }), 200
    else:
        return jsonify({
            "message": f"Captura activa para {interfaz} en {host}",
            "estdo": "Error"
        }), 400

# Delete - Para la captura de traps linkup y linkdown de una interfaz en especifico, retornar json con el estado de la interfaz
@routers_bp.route("/<host>/interfaces/<path:interfaz>/estado", methods=["DELETE"])
def detener_traps_interfaz(host, interfaz):
    ok = traps_service.stop_trap_capture(host, interfaz)
    estado = traps_service.get_interface_trap_status(host, interfaz)

    if ok:
        return jsonify({
            "message": f"captura de traps detenida en {interfaz} en el host: {host}",
            "estado": estado
        }), 200
    else:
        return jsonify({
            "message": f"No hay captura activa para {interfaz} en {host}",
            "estado": "inexistente"
        }), 400

# Grafica Traps
@routers_bp.route("/<host>/interfaces/<path:interfaz>/grafica_traps", methods=["GET"])
def obtener_grafica_traps(host, interfaz):
    filename = f"data/traps_{host.replace('.', '')}{interfaz.replace('/', '_')}.json"
    if not os.path.exists(filename):
        return jsonify({"error": "No hay traps registrados para graficar"}), 404
    
    with open(filename, "r") as f:
        traps = json.load(f)
    
    if not traps:
        return jsonify({"error":"El archivo existe pero no contiene traps"}), 400
    
    timestamps = [entry["timestamp"] for entry in traps]
    estados = [1 if entry["type"] == "linkUp" else 0 for entry in traps]

    plt.figure(figsize=(10, 6))
    plt.step(timestamps, estados, where='post')
    plt.yticks([0, 1], ["linkDown", "linkUp"])
    plt.xticks(rotation=45)
    plt.title(f"Traps linkUp/linkDown para {interfaz} ({host})")
    plt.xlabel("Tiempo")
    plt.ylabel("Estado")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return send_file(img, mimetype="image/png")
