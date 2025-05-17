from snmp.snmp_sender import RouterSNMPClient

class TopologyService:
    def __init__(self, routers):
        self.router = next((r for r in routers if r.get("name") == "R4.redes.local"), None)
        
        if self.router is None:
            raise ValueError("Router 'R4.redes.local' no encontrado")
    
    async def get_topology(self):
        client = RouterSNMPClient(self.router["ip"], self.router["name"], self.router.get("community", "public"))
        
        info = await client.discover_network()

        return info