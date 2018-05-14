import networkx as nx
import matplotlib.pyplot as plt


def draw(v, k, l, u, matrices):
    for i, matrix in enumerate(matrices):

        fig = plt.figure()

        nodes = {n: str(n) for n in range(v)}
        graph = nx.Graph()
        graph.add_nodes_from(nodes.keys())

        pos = nx.circular_layout(graph)
        nx.draw_networkx_labels(graph, pos, nodes)

        for r, c in zip(*matrix.nonzero()):
            graph.add_edge(r, c)

        nx.draw_circular(graph)

        plt.axis('equal')
        fig.savefig(f'srg_{v}_{k}_{l}_{u}_{i}.png')
