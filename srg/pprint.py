import click
from functools import partial, reduce


def _compose2(f, g):
    return lambda *a, **kw: f(g(*a, **kw))


def compose(*fs):
    return reduce(_compose2, fs)



_print = lambda *args, **kwargs : click.secho(repr(*args), **kwargs)

green = partial(_print, fg='green')
blue = partial(_print, fg='blue')
red = partial(_print, fg='red')
yellow = partial(_print, fg='yellow')

clear = click.clear