import ujson


class JsonSerializableModel:
  ''' Base class which adds a __json__method which provides json for ujson '''

  # Whitelist of object properties to be given when serialized to json
  json_fields = ()

  def __json__(self):
    ''' Return generated json to ujson for this object instance, using the fields defined in parent '''
    return ujson.dumps({key: getattr(self, key) for key in self.json_fields})
