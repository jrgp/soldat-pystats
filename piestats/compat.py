# Helpers to convert byte responses from redis and log lines to strings

# There are likely lots more relevant encodings that are missing
encodings = ('utf-8', 'cp1252', 'cp1251', 'cp1250', 'cp1140', 'cp1254', 'cp1256')


def kill_bytes(item):
  ''' Given a single variable, if it is bytes decode to string '''
  if isinstance(item, bytes):
    last_exception = None

    # Try some known encodings
    for encoding in encodings:
      try:
        return item.decode(encoding)
      except UnicodeDecodeError as e:
        last_exception = e

    # If none work, raise the last exception we got
    raise last_exception

  else:
    return item


def strip_bytes_from_list(iterable):
  ''' Given iterable, convert each item within to a string if it is bytes '''
  if not iterable:
    return iterable

  return [kill_bytes(item) for item in iterable]


def strip_bytes_from_stream(stream):
  '''
    Given an iterable of lists/tuples, yield each list/tuple back with the items inside converted to non-bytes
    Good for ZREVRANGE WITHSCORES
  '''
  if not stream:
    return stream

  for item in stream:
    if isinstance(item, (list, tuple)):
      yield strip_bytes_from_list(item)
    else:
      yield kill_bytes(item)


def strip_bytes_from_dict(d):
  ''' Given a dict, return it with bytes replaced with strings in both keys and values '''
  if isinstance(d, dict):
    return {kill_bytes(key): kill_bytes(value) for key, value in d.items()}
  else:
    return d
