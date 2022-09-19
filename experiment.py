from two_dist_set import util
from two_dist_set import strong_graph

v, k, l, u = 21, 10, 5, 4

seed = util.generate_seed(v, k, l, u)
lst : list = [seed]
while lst:
    # q = lst.pop(0) # pop first, lst[0].
    q = lst.pop() # pop last, lst[-1].
    sublst : list = list(strong_graph._advance_from_partition(q))
    lst += sublst