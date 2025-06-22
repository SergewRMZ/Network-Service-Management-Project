import asyncio
import time
import json
import os
import threading
from snmp.snmp_sender import RouterSNMPClient
from datetime import datetime

class MonitorService:
    def __init__(self, routers):
        self.routers = routers
        self.tasks = {}

    def _get_router(self, host):
        for router in self.routers:
            if router["ip"] == host or router.get("hostname") == host:
                return router
        return None

    def _get_filename(self, host, interface):
        filename = f"data/{host.replace('.', '_')}_{interface.replace('/', '_')}.json"
        os.makedirs("data", exist_ok=True)
        return filename

    async def _monitor_octets(self, host, interface, interval, duration):
        print(f"Iniciando monitoreo de {interface} en {host} cada {interval} segundos por {duration}")

        router = self._get_router(host)
        if not router:
            return

        client = RouterSNMPClient(router["ip"], router["name"], router.get("community", "public"))

        interfaces = await client.get_interface_info()
        idx = next((i["numero"] for i in interfaces if i["nombre"] == interface), None)
        if idx is None:
            print(f"Interfaz {interface} no encontrada en {host}")
            return

        oid = f"1.3.6.1.2.1.2.2.1.10.{idx}"
        filename = self._get_filename(host, interface)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            value = await client.snmp_get(oid)
            timestamp = datetime.utcnow().isoformat() + "Z"

            if value is not None:
                entry = {"timestamp": timestamp, "octetos": int(value)}

                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        data = json.load(f)
                else:
                    data = []

                data.append(entry)

                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)

                print(f"[{host} - {interface}] Octetos: {value}")

            await asyncio.sleep(interval)
        print(f"Monitoreo terminado para {interface} en {host} tras {duration} segundos.")
    def start_monitoring(self, host, interface, interval, duration):
        key = (host, interface)
        if key in self.tasks:
            return False

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self._monitor_octets(host, interface, interval, duration))
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()

        self.tasks[key] = task
        return True


    def stop_monitoring(self, host, interface):
        key = (host, interface)
        task = self.tasks.pop(key, None)
        if task:
            task.cancel()
            return True
        return False
