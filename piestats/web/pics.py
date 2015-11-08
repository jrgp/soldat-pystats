from flask import url_for


def gunpic(gun):
  filename = 'soldatguns/{gun}.png'.format(gun=gun.replace(' ', '_'))
  return url_for('static', filename=filename)
