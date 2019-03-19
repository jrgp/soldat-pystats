from piestats.models.base import JsonSerializableModel
import ujson


def test_json_serializer():

  class FakeModel(JsonSerializableModel):
    json_fields = ('foo', 'bar')

    def __init__(self):
      self.foo = 'foobar1'
      self.bar = 'foobar2'

  model = FakeModel()

  assert ujson.loads(ujson.dumps(model)) == {'foo': 'foobar1', 'bar': 'foobar2'}
