from flask import Flask, render_template
from piestats.results import stats

app = Flask(__name__)


@app.route('/player/<string:name>')
def player(name):
  player = stats().get_player(name)
  if not player:
    return render_template('player_not_found.html')
  return render_template('player.html', player=player)


@app.route('/')
def index():
  s = stats()
  return render_template('index.html',
                         top=s.get_top_killers(),
                         kills=s.get_last_kills())


def main():
  app.run(host='0.0.0.0', debug=True)
