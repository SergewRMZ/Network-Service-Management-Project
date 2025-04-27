import asyncio
from pysnmp.hlapi.v3arch.asyncio import *
from snmp.snmp_sender import RouterSNMPClient
from services.routers_service import RouterService
from services.topology_service import TopologyService
from config import ROUTERS
import networkx as nx
import matplotlib.pyplot as plt

async def run():
    service = TopologyService(ROUTERS)

    result = await service.get_topology()

    print(result)

    plot_network(result)


def plot_network(connections, file_name="network_graph.png"):
    """
    Function to plot the connections between routers and save the image.

    Parameters:
    - connections: a set of tuples where each tuple contains two connected routers.
    - file_name: the name of the file to save the image (default is "network_graph.png").
    """
    # Create an undirected graph
    G = nx.Graph()

    # Add the connections to the graph
    G.add_edges_from(connections)

    # Draw the graph
    plt.figure(figsize=(10, 8))
    nx.draw(G, with_labels=True, node_size=3000, node_color='skyblue', font_size=10, font_weight='bold', edge_color='gray')
    plt.title("Router Network Connections")

    # Save the graph as an image file
    plt.savefig(file_name, format="png")
    print(f"Graph saved as {file_name}")

asyncio.run(run())
