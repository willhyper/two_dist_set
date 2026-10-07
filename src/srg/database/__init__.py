'''
https://www.win.tue.nl/~aeb/graphs/srg/srgtab.html
http://www.maths.gla.ac.uk/~es/srgraphs.php

Reading Brouwer's tables (https://aeb.win.tue.nl/graphs/srg/srgtab1-50.html, srgtab51-100.html, ...)
-----------------------------------------------------------------------------------------------------
The site only calls the first column "existence" and does not document its symbols. This reading was
worked out from the data and checked against this repo (e.g. (16,6,2,2) is "2!" and has 2 isomorphism
classes here, (28,12,6,4) is "4!" and the solver finds exactly those 4, (21,10,4,5) is "-" and the
solver finds none):

    !        exactly ONE graph (unique)
    N!       exactly N non-isomorphic graphs, a complete enumeration. NOT a factorial:
             "15!" means 15 graphs, "2!" means 2 graphs.
    +        exists; more than one graph is known but the full count is not settled
    -        does not exist
    ?        existence is open
    (blank)  the complement of the previous parameter set (same verdict, same number of graphs)

Row colour says the same thing: green = exists, red = does not exist, yellow = open.
A graph and its complement are both SRGs, so only one of each pair has to be solved, see build.py.

Problem files (problem_V_K_L_U.py)
----------------------------------
v, k, l, u, and solutions: list[str] of plain-text 0/1 grids (see codec.py; get_solutions() decodes them).
  - a docstring starting "no solution." and no `status` variable: the solver proved that no such SRG exists
  - `status = 'todo'` (or 'undecided'): a placeholder, the empty solutions list proves NOTHING; the docstring
    starts with a STATUS line saying whether it is still to be tackled, undecided after a time limit, or a
    complement to derive
  - otherwise solutions holds one matrix per isomorphism class found, which may be fewer than the table's count
'''

def list_problems():
    import pkgutil
    problem_solutions = [m.name for m in pkgutil.iter_modules(__path__) if m.name.startswith('problem')]
    return problem_solutions

def extract_vklu(problem : str):
    _, *vklu = problem.split('_')
    return list(map(int, vklu))

def get_solutions(v,k,l,u) -> list:
    '''the stored solutions as numpy int8 matrices (problem files store them as text, see codec.py)'''
    import importlib
    from .codec import decode
    name = __package__ + f'.problem_{v}_{k}_{l}_{u}'
    m = importlib.import_module(name)
    return [decode(s) if isinstance(s, str) else s for s in m.solutions]


def draw(v, k, l, u):
    import networkx as nx
    import matplotlib.pyplot as plt
    matrices = get_solutions(v,k,l,u)
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
        pngname = f'srg_{v}_{k}_{l}_{u}_{i}.png'
        fig.savefig(pngname)
        print(f'srg_{v}_{k}_{l}_{u}_{i}.png')