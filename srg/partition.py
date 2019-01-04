
def enum(s: int, bounds) -> tuple:
    assert s >= 0, "sum to be placed is required >= 0"

    l = len(bounds)
    assert l >= 1, "len(dict) is required >= 1"

    bound, *others = bounds

    if l > 1:

        for v in range(min(bound, s) + 1):
            rem = s - v

            for t in enum(rem, others):
                yield (v,) + t

    else:
        if s <= bound:
            yield (s,)


if __name__ == '__main__':
    bounds = [1, 1, 1, 1, 1]
    for e in enum(3, bounds): print(e)
