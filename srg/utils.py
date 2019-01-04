from .srg import Question
from . import pprint


def debug(func):

    def wrapper(Q:Question):
        Q_before = Q.copy()

        result = func(Q)
        if Q == Q_before:
            pprint.blue(f'performing {func.__name__}. No change')
        else:
            print(Q_before)
            pprint.green(f'performing {func.__name__}. reduce to')
            print(Q)


        try:
            Q._invariant_check()
        except AssertionError as e:

            print(Q_before)
            pprint.red(f'performing {func.__name__}. AssertionError!')
            print(Q)

            print()

            raise e

        return result

    return wrapper if __debug__ else func

