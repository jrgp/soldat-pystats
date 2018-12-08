import re
trailing_name_count_matcher = re.compile('(.+)\((\d+)\)$')


def remove_redundant_player_names(names):
  '''
    Given a list of names, remove ones with trailing (1) through (n) depending on correctness
    Assumes names will be a list of strings with no duplicates. Order is preserved on return
  '''

  if len(names) == 1:
      return names

  original_names = set(names)

  for name in list(names):
      m = trailing_name_count_matcher.match(name)
      if m:
          prefix, count = m.groups()
          count = int(count)
          if (count == 1 and prefix in original_names) or (count > 1 and '%s(%d)' % (prefix, count - 1) in original_names):
              names.remove(name)

  return names


class PaginationHelper():
    def __init__(self, bare_route, offset, interval=20, num_items=None):
        self.bare_route = bare_route
        self.interval = interval
        self.num_items = num_items

        if offset % interval or offset < 0:
            offset = 0

        self.offset = offset

    @property
    def prev_url(self):
        if self.offset is None:
            return False

        elif self.offset == self.interval:
            return self.bare_route
        elif self.offset >= self.interval:
            return self.bare_route + '/pos/%d' % (self.offset - self.interval)

    @property
    def next_url(self):
        if (self.offset + self.interval) > self.num_items:
            return False
        return self.bare_route + '/pos/%d' % (self.offset + self.interval)
