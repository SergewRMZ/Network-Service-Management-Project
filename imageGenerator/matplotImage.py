import networkx as nx
import matplotlib.pyplot as plt

class MatplotImage:
    def __init__(self):
        pass

    def plot_network(self, connections, file_name="network_graph.png"):
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
