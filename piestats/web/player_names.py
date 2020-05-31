import re
trailing_name_count_matcher = re.compile(r'(.+)\((\d+)\)$')


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
