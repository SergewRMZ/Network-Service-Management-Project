import threading
import json
import time
import os
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413 import cmdgen

class TrapsService:
    def __init__(self, routers):
        self.routers = routers
        self.trap_threads = {}  # {(host, interfaz): thread}

    def get_interface_trap_status(self, host, interfaz):
        key = (host, interfaz)
        activo = key in self.trap_threads
        filename = f"data/traps_{host.replace('.', '')}{interfaz.replace('/', '_')}.json"
        hay_datos = os.path.exists(filename)
        return {
            "router": host,
            "interfaz": interfaz,
            "captura_activa": activo,
            "archivo_datos": hay_datos
        }

    def start_trap_capture(self, host, interfaz):
        key = (host, interfaz)
        if key in self.trap_threads:
            return False  # Ya hay un monitoreo activo

        def capture():
            filename = f"data/traps_{host.replace('.', '')}{interfaz.replace('/', '_')}.json"
            traps = []

            snmpEngine = SnmpEngine()
            transport = UdpTransportTarget(('0.0.0.0', 162))  
            def handle_trap(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
                trap_type = "linkUp" if 'linkUp' in str(varBinds) else "linkDown"
                traps.append({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": trap_type,
                    "varBinds": str(varBinds)
                })

                with open(filename, "w") as f:
                    json.dump(traps, f, indent=2)

            trapReceiver = AsyncNotificationReceiver(snmpEngine, handle_trap)

            snmpEngine.transportDispatcher.jobStarted(1)

            snmpEngine.transportDispatcher.runDispatcher()

        # Inicia el hilo para la captura
        t = threading.Thread(target=capture, daemon=True)
        self.trap_threads[key] = t
        t.start()
        return True

    def stop_trap_capture(self, host, interfaz):
        key = (host, interfaz)
        if key in self.trap_threads:
            del self.trap_threads[key]
            return True
        return False
