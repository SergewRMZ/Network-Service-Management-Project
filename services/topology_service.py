from snmp.snmp_sender import RouterSNMPClient

class TopologyService:
    def __init__(self, routers):
        self.router = routers[3]
    
    async def get_topology(self):
        client = RouterSNMPClient(self.router["ip"], self.router["name"], self.router.get("community", "public"))
        
        info = await client.discover_network()

        return info