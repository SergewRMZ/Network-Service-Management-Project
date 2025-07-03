import os
import json
import threading
from datetime import datetime
from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher
from pysnmp.carrier.asyncio.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
import asyncio


class TrapsService:
    def __init__(self, routers):
        self.routers = routers
        self.active_traps = {}
        os.makedirs('data', exist_ok=True)

        # Iniciar el receptor en un hilo separado, con su propio event loop
        threading.Thread(target=self._start_trap_receiver, daemon=True).start()

    def _start_background_trap_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._start_trap_receiver()
        loop.run_forever()

    def _start_trap_receiver(self):
        asyncio.set_event_loop(asyncio.new_event_loop()) 
        dispatcher = AsyncioDispatcher()
        dispatcher.register_recv_callback(self._trap_callback)

        try:
            dispatcher.register_transport(
                udp.DOMAIN_NAME,
                udp.UdpAsyncioTransport().open_server_mode(('0.0.0.0', 162))
            )
        except Exception as e:
            print(f"❌ Error ligando al puerto 162: {e}")
            return

        dispatcher.job_started(1)
        print("🚀 Receptor SNMP escuchando en el puerto 162")

        try:
            dispatcher.runDispatcher()
        except Exception as e:
            print(f"❌ Error en el dispatcher: {e}")
        finally:
            dispatcher.closeDispatcher()

    def _trap_callback(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):

        src_ip, _ = transportAddress
        while wholeMsg:
            msgVer = int(api.decodeMessageVersion(wholeMsg))
            if msgVer not in api.PROTOCOL_MODULES:
                print(f"❌ Versión SNMP no soportada: {msgVer}")
                return

            pMod = api.PROTOCOL_MODULES[msgVer]
            reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
            reqPDU = pMod.apiMessage.get_pdu(reqMsg)

            if not (reqPDU.isSameTypeWith(pMod.TrapPDU()) or reqPDU.isSameTypeWith(pMod.SNMPv2TrapPDU())):
                return

            varBinds = (
                pMod.apiTrapPDU.get_varbinds(reqPDU)
                if msgVer == api.SNMP_VERSION_1
                else pMod.apiPDU.get_varbinds(reqPDU)
            )

            timestamp = datetime.utcnow().isoformat() + "Z"
            trap_type = "desconocido"
            trap_data = {}

            for oid, val in varBinds:
                oid_str = str(oid)
                val_str = str(val)
                trap_data[oid_str] = val_str

                if oid_str == "1.3.6.1.6.3.1.1.4.1.0":
                    if val_str.endswith("linkUp"):
                        trap_type = "linkUp"
                    elif val_str.endswith("linkDown"):
                        trap_type = "linkDown"

                if oid_str == "1.3.6.1.6.3.1.1.5.3":
                    trap_type = "linkDown"
                elif oid_str == "1.3.6.1.6.3.1.1.5.4":
                    trap_type = "linkUp"

            print(f"📡 Trap {trap_type} desde {src_ip} @ {timestamp}")

            for (host, interfaz), _ in list(self.active_traps.items()):
                if host == src_ip:
                    filename = f"data/traps_{host.replace('.', '')}_{interfaz.replace('/', '_')}.json"
                    traps = []
                    if os.path.exists(filename):
                        with open(filename) as f:
                            traps = json.load(f)

                    traps.append({
                        "timestamp": timestamp,
                        "type": trap_type,
                        "vars": trap_data
                    })

                    with open(filename, 'w') as f:
                        json.dump(traps, f, indent=2)

    def get_interface_trap_status(self, host, interfaz):
        key = (host, interfaz)
        activo = key in self.active_traps
        filename = f"data/traps_{host.replace('.', '')}_{interfaz.replace('/', '_')}.json"
        hay_datos = os.path.exists(filename)
        return {
            "router": host,
            "interfaz": interfaz,
            "captura_activa": activo,
            "archivo_datos": hay_datos
        }

    def start_trap_capture(self, host, interfaz):
        key = (host, interfaz)
        if key in self.active_traps:
            return False
        self.active_traps[key] = True
        return True

    def stop_trap_capture(self, host, interfaz):
        key = (host, interfaz)
        if key in self.active_traps:
            del self.active_traps[key]
            return True
        return False
