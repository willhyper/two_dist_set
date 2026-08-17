from itertools import combinations
from srg import partition


def test_enum_contract():
    '''
    enum(s, bounds) yields every vector of len(bounds) whose entries sum to s
    and are each <= the corresponding bound.
    '''
    s = 3
    bounds = [1, 1, 1, 1, 1]

    results = list(partition.enum(s, bounds))

    for vec in results:
        assert len(vec) == len(bounds)
        assert sum(vec) == s
        assert all(v <= b for v, b in zip(vec, bounds))

    # bounds are all 1, so this is exactly "choose 3 of 5 positions to be 1"
    expected = {tuple(1 if i in combo else 0 for i in range(5))
                for combo in combinations(range(5), 3)}
    assert set(results) == expected
