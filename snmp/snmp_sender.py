import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, UdpTransportTarget, CommunityData,
    ContextData, ObjectType, ObjectIdentity,
    get_cmd, next_cmd
)
from pysnmp.smi import builder, view
from pysnmp.proto.rfc1902 import ObjectName

class RouterSNMPClient:
    def __init__(self, host, name, community='public', port=161):
        self.host = host
        self.community = community
        self.port = port
        self.name = name


    async def snmp_get(self, oid):
        snmpEngine = SnmpEngine()
        transport = await UdpTransportTarget.create((self.host, self.port))
        result = await get_cmd(
            snmpEngine,
            CommunityData(self.community, mpModel=1),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        errorIndication, errorStatus, errorIndex, varBinds = result

        if errorIndication or errorStatus:
            return None
        return varBinds[0][1].prettyPrint()

    async def snmp_walk(self, oid):
        snmpEngine = SnmpEngine()
        result = []

        transport = await UdpTransportTarget.create((self.host, self.port))

        mibViewController = view.MibViewController(snmpEngine.get_mib_builder())

        base_oid_obj = ObjectIdentity(oid).resolveWithMib(mibViewController).getOid()
        base_oid = ObjectName(base_oid_obj)
        current_oid = ObjectIdentity(oid)

        while True:
            iterator = next_cmd(
                snmpEngine,
                CommunityData(self.community, mpModel=1),
                transport,
                ContextData(),
                ObjectType(current_oid),
                lexicographicMode=False
            )

            errorIndication, errorStatus, errorIndex, varBinds = await iterator

            if errorIndication:
                print(f"Error: {errorIndication}")
                break
            elif errorStatus:
                print(f"Error Status: {errorStatus.prettyPrint()}")
                break
            elif not varBinds:
                break
            else:
                for varBind in varBinds:
                    name, val = varBind
                    current_oid_obj = ObjectName(name)

                    if not current_oid_obj[:len(base_oid)] == base_oid:
                        return result

                    result.append((str(name), val.prettyPrint()))
                    current_oid = ObjectIdentity(name)

        return result

    async def get_interface_info(self):
        if_types = await self.snmp_walk('1.3.6.1.2.1.2.2.1.3')
        if_statuses = await self.snmp_walk('1.3.6.1.2.1.2.2.1.8')
        if_names = await self.snmp_walk('1.3.6.1.2.1.31.1.1.1.1')

        ip_to_index = await self.snmp_walk('1.3.6.1.2.1.4.20.1.2')
        subnet_masks = await self.snmp_walk('1.3.6.1.2.1.4.20.1.3')

        interfaces = []

        for name_oid, name in if_names:
            index = int(name_oid.split('.')[-1])
            type_oid = f'1.3.6.1.2.1.2.2.1.3.{index}'
            status_oid = f'1.3.6.1.2.1.2.2.1.8.{index}'

            tipo = next((v for k, v in if_types if k.endswith(f'.{index}')), 'desconocido')
            estado_val = next((v for k, v in if_statuses if k.endswith(f'.{index}')), 'desconocido')

            estado = {
                '1': 'up',
                '2': 'down',
                '3': 'testing'
            }.get(estado_val, 'desconocido')

            ip = None
            mascara = None

            for ip_oid, idx in ip_to_index:
                if int(idx) == index:
                    ip = ip_oid.split('.')[-4:]
                    ip = '.'.join(ip)
                    mask = next((m for k, m in subnet_masks if k.endswith(ip)), None)
                    if mask:
                        mascara = mask
                    break

            interfaces.append({
                "nombre": name,
                "numero": index,
                "tipo": tipo,
                "ip": ip or "No asignada",
                "mascara": mascara or "Desconocida",
                "estado": estado
            })

        return interfaces

    async def get_general_info(self, rol=None, empresa=None):
        nombre = await self.snmp_get('1.3.6.1.2.1.1.5.0')
        hex_os = await self.snmp_get('1.3.6.1.2.1.1.1.0')
        decoded_os = self.decode_hex_string(hex_os)
        
        status_list = await self.snmp_walk('1.3.6.1.2.1.2.2.1.8') 
        names_list = await self.snmp_walk('1.3.6.1.2.1.2.2.1.2')


        interface_names = {
            int(oid.split('.')[-1]): name
            for oid, name in names_list
        }

        interfaces_status = []
        for oid, state in status_list:
            index = int(oid.split('.')[-1])
            if state == '1':  # 1 = up
                int_name = interface_names.get(index, f"Desconocida {index}")
                interfaces_status.append({
                    "nombre": int_name,
                    "estado": "activa"
                })

        return {
            "host": self.host,
            "nombre": nombre,
            "ip_administrativa": self.host,
            "sistema_operativo": decoded_os,
            "empresa": empresa or "Desconocida",
            "rol": rol or "No definido",
            "interfaces": interfaces_status
        }

    def get_loopback_ip(self, ips):
        for ip in ips:
            if ip.startswith("127.") or ip.startswith("10.") or ip.startswith("172."):
                return ip
        return ips[0] if ips else "No encontrada"

    def decode_hex_string(self,hex_str):
        try:
            bytes_object = bytes.fromhex(hex_str.replace("0x", ""))
            return bytes_object.decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error decoding: {e}"
    
    async def get_router_neighbors(self):
        try:
            # Obtener nombres de los vecinos (routers)
            names = await self.snmp_walk('1.3.6.1.4.1.9.9.23.1.2.1.1.6')  # Neighbor name
            # Obtener las IPs de los vecinos
            ips = await self.snmp_walk('1.3.6.1.4.1.9.9.23.1.2.1.1.4')  # Neighbor IP

            # Filtrar y obtener solo los routers, ya que no hay más detalles necesarios
            routers = []
            for i in range(len(names)):
                router = {
                    "nombre": names[i][1],
                    "ip": self.parse_ip_from_hex(ips[i][1])
                }
                routers.append(router)

            return routers
        except Exception as e:
            print(f"Error obteniendo vecinos CDP: {e}")
            return []
    
    async def discover_network(self, visited=None, discovered=None):
        if visited is None:
            visited = set()
        if discovered is None:
            discovered = set()

        if self.host in visited:
            return set()

        visited.add(self.host)
        discovered.add(self.name)  # mark the router name as discovered

        neighbors = await self.get_router_neighbors()

        connections = set()

        # Only add connection if the neighbor will be reachable
        for neighbor in neighbors:
            from_device = self.name
            to_device = neighbor["nombre"]

            connections.add((from_device, to_device))

        # Now visit neighbors recursively
        for neighbor in neighbors:
            ip = neighbor["ip"]
            name = neighbor["nombre"]

            if ip and ip not in visited:
                new_client = RouterSNMPClient(ip, name, self.community, self.port)
                try:
                    new_connections = await new_client.discover_network(visited, discovered)
                    connections.update(new_connections)
                except Exception as e:
                    print(f"Could not access {ip}: {e}")

        # Final filtering step: only keep connections where both routers were discovered
        final_connections = set()
        for a, b in connections:
            if a in discovered and b in discovered:
                # sort to avoid duplicates (R1,R2) and (R2,R1)
                final_connections.add(tuple(sorted((a, b))))

        return final_connections

    def parse_ip_from_hex(self, hex_str):
        """Convierte un string hex a una dirección IP (ej. '0xC0A80101' -> '192.168.1.1')"""
        if hex_str.startswith("0x"):
            hex_str = hex_str[2:]
        ip = [str(int(hex_str[i:i+2], 16)) for i in range(0, len(hex_str), 2)]
        return '.'.join(ip)
    
    def simplificar_conexiones(self, red):
        simplified_connections = set()

        for ip, router in red:
            # Obtener solo el nombre del router (sin el dominio)
            connected_router = router.split('.')[0]
            for other_ip, other_router in red:
                # Obtener solo el nombre del otro router
                other_connected_router = other_router.split('.')[0]
                if router != other_router:
                    # Añadir la conexión entre los routers de manera ordenada
                    simplified_connections.add(tuple(sorted([connected_router, other_connected_router])))

        return simplified_connections