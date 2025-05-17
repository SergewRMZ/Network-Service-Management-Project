from snmp.snmp_sender import RouterSNMPClient  # Asumo que tu clase RouterSNMPClient está ahí

class RouterService:
    def __init__(self, routers):
        self.routers = routers

    def _get_router(self, host):
        for router in self.routers:
            if router["ip"] == host or router.get("hostname") == host:
                return router
        return None

    async def get_all_router_info(self):
        routers_info = []
        for router in self.routers:
            client = RouterSNMPClient(router["ip"], router["name"], router.get("community", "public"))
            info = await client.get_general_info(
                rol=router.get("rol") or "Indefinido",
                empresa=router.get("empresa") or "Indefinido"
            )
            routers_info.append(info)
        return routers_info

    async def get_router_info(self, host):
        router = self._get_router(host)
        if not router:
            return None
        client = RouterSNMPClient(router["ip"], router["name"], router.get("community", "public"))
        
        return await client.get_general_info(
            rol=router.get("rol"),
            empresa=router.get("empresa")
        )
    
    async def get_interface_info(self, host):
        router = self._get_router(host)
        if not router:
            return None
        
        client = RouterSNMPClient(router["ip"], router["name"], router.get("community", "public"))
        
        return await client.get_interface_info()
