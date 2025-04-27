from flask import Blueprint, jsonify, request
from services.topology_service import TopologyService
from config import ROUTERS
import asyncio
import threading
import time
import os
import json

topology_bp = Blueprint('topology', __name__)
service = TopologyService(ROUTERS)

demonio_thread = None
demonio_running = False
demonio_interval = 300  # 5 minutos en segundos

def demonio_func():
    global demonio_running, demonio_interval

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while demonio_running:
        print("Explorando la red...")

        topology_set = loop.run_until_complete(service.get_topology())
        topology = list(topology_set)

        with open("topology.json", "w") as f:
            json.dump(topology, f)

        time.sleep(demonio_interval)

@topology_bp.route("/", methods=["GET"])
def get_topology():
    if os.path.exists("topology.json"):
        with open("topology.json", "r") as f:
            topology = json.load(f)
    else:
        topology_set = asyncio.run(service.get_topology())
        topology = list(topology_set)
        with open("topology.json", "w") as f:
            json.dump(topology, f)

    return jsonify(topology), 200

@topology_bp.route("/", methods=["POST", "PUT"])
def start_or_update_demonio():
    global demonio_thread, demonio_running, demonio_interval

    # Leer nuevo intervalo si viene en el body
    if request.method == "PUT":
        data = request.get_json()
        new_interval = data.get("interval")
        if new_interval:
            demonio_interval = int(new_interval)
            return jsonify({"message": f"Intervalo actualizado a {demonio_interval} segundos."}), 200

    if not demonio_running:
        demonio_running = True
        demonio_thread = threading.Thread(target=demonio_func, daemon=True)
        demonio_thread.start()
        return jsonify({"message": "Demonio iniciado."}), 200
    else:
        return jsonify({"message": "Demonio ya está corriendo."}), 200

@topology_bp.route("/", methods=["DELETE"])
def stop_demonio():
    global demonio_running
    if demonio_running:
        demonio_running = False
        return jsonify({"message": "Demonio detenido."}), 200
    else:
        return jsonify({"message": "No hay demonio corriendo."}), 400