# Import necessary libraries for asynchronous SNMP queries
import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, UdpTransportTarget, CommunityData,
    ContextData, ObjectType, ObjectIdentity,
    get_cmd, next_cmd
)
from pysnmp.smi import builder, view
from pysnmp.proto.rfc1902 import ObjectName

# Main class to interact with a router using SNMP
class RouterSNMPClient:
    # Constructor
    def __init__(self, host, name, community='public', port=161):
        self.host = host                  # IP or hostname of the router
        self.community = community        # SNMP community string (default: 'public')
        self.port = port                  # SNMP port (default: 161)
        self.name = name                  # Name to identify the router

    # Performs a single SNMP GET query for one OID
    async def snmp_get(self, oid):
        snmpEngine = SnmpEngine()
        transport = await UdpTransportTarget.create((self.host, self.port))  # Set up transport
        result = await get_cmd(
            snmpEngine,
            CommunityData(self.community, mpModel=1),  # mpModel=1 means SNMPv2c
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid))            # The OID to query
        )

        errorIndication, errorStatus, errorIndex, varBinds = result

        if errorIndication or errorStatus:
            return None  # Return None if there was an error
        return varBinds[0][1].prettyPrint()  # Return the value as a string

    # Performs an SNMP WALK on a base OID (walks through sub-OIDs)
    async def snmp_walk(self, oid):
        snmpEngine = SnmpEngine()
        result = []

        transport = await UdpTransportTarget.create((self.host, self.port))

        # Create a MIB view to resolve object names
        mibViewController = view.MibViewController(snmpEngine.get_mib_builder())

        base_oid_obj = ObjectIdentity(oid).resolveWithMib(mibViewController).getOid()
        base_oid = ObjectName(base_oid_obj)
        current_oid = ObjectIdentity(oid)

        while True:
            # Perform the next SNMP query in the hierarchy
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
                        return result  # Stop if OID is outside the base OID subtree

                    result.append((str(name), val.prettyPrint()))
                    current_oid = ObjectIdentity(name)

        return result  # Returns a list of (OID, value) tuples

    # Retrieves detailed information about the router's interfaces
    async def get_interface_info(self):
        # Query multiple interface attributes
        if_types = await self.snmp_walk('1.3.6.1.2.1.2.2.1.3')   # Interface type
        if_statuses = await self.snmp_walk('1.3.6.1.2.1.2.2.1.8') # Interface status
        if_names = await self.snmp_walk('1.3.6.1.2.1.31.1.1.1.1') # Logical interface name

        ip_to_index = await self.snmp_walk('1.3.6.1.2.1.4.20.1.2') # Maps IPs to interface index
        subnet_masks = await self.snmp_walk('1.3.6.1.2.1.4.20.1.3') # Maps IPs to subnet masks

        interfaces = []

        for name_oid, name in if_names:
            index = int(name_oid.split('.')[-1])  # Extract interface index
            type_oid = f'1.3.6.1.2.1.2.2.1.3.{index}'
            status_oid = f'1.3.6.1.2.1.2.2.1.8.{index}'

            tipo = next((v for k, v in if_types if k.endswith(f'.{index}')), 'unknown')
            estado_val = next((v for k, v in if_statuses if k.endswith(f'.{index}')), 'unknown')

            # Map SNMP status code to human-readable text
            estado = {
                '1': 'up',
                '2': 'down',
                '3': 'testing'
            }.get(estado_val, 'unknown')

            ip = None
            mask = None

            for ip_oid, idx in ip_to_index:
                if int(idx) == index:
                    ip_parts = ip_oid.split('.')[-4:]  # Extract IP address from OID
                    ip = '.'.join(ip_parts)
                    mask = next((m for k, m in subnet_masks if k.endswith(ip)), None)
                    break

            interfaces.append({
                "nombre": name,
                "numero": index,
                "tipo": tipo,
                "ip": ip or "Unassigned",
                "mascara": mask or "Unknown",
                "estado": estado
            })

        return interfaces  # List of interfaces with detailed info

    # Retrieves general information about the router: system name, OS, active interfaces, etc.
    async def get_general_info(self, rol=None, empresa=None):
        nombre = await self.snmp_get('1.3.6.1.2.1.1.5.0')         # System name
        hex_os = await self.snmp_get('1.3.6.1.2.1.1.1.0')         # OS in hexadecimal format
        decoded_os = self.decode_hex_string(hex_os)              # Decode hex to readable string
        
        status_list = await self.snmp_walk('1.3.6.1.2.1.2.2.1.8') # Interface status list
        names_list = await self.snmp_walk('1.3.6.1.2.1.2.2.1.2')  # Interface name list

        # Map interface index to names
        interface_names = {
            int(oid.split('.')[-1]): name
            for oid, name in names_list
        }

        interfaces_status = []
        for oid, state in status_list:
            index = int(oid.split('.')[-1])
            if state == '1':  # Only include active interfaces
                int_name = interface_names.get(index, f"Unknown {index}")
                interfaces_status.append({
                    "nombre": int_name,
                    "estado": "active"
                })

        # Return all general information
        return {
            "nombre": nombre,
            "sistema_operativo": decoded_os,
            "interfaces_activas": interfaces_status,
            "rol": rol,
            "empresa": empresa
        }

    # Helper function to decode hexadecimal strings into plain text
    def decode_hex_string(self, hex_string):
        try:
            if hex_string.startswith("0x"):
                hex_string = hex_string[2:]  # eliminar "0x"
            hex_string = hex_string.replace(" ", "").replace("\n", "")
            bytes_data = bytes.fromhex(hex_string)
            return bytes_data.decode('utf-8', errors='ignore')
        except Exception:
            return hex_string
    
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
    