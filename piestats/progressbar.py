import click


def simple_progressbar(items, **kwargs):
  ''' Wrap click's progress bar in a simple generator. Avoid needing to use its context manager. '''
  kwargs.setdefault('show_eta', False)
  with click.progressbar(items, **kwargs) as progressbar:
    for item in progressbar:
      yield item
