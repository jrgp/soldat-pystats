from flask import Flask, render_template, url_for
from piestats.results import stats
from piestats.web.pics import gunpic
from datetime import datetime

app = Flask(__name__)


@app.route('/player/<string:name>')
def player(name):
  player = stats().get_player(name)
  if not player:
    return render_template('player_not_found.html')
  return render_template('player.html', player=player, gunpic=gunpic)


@app.route('/kills', defaults=dict(startat=0))
@app.route('/kills/pos/<int:startat>')
def latestkills(startat):
  s = stats()

  if (startat % 20):
    startat = 0

  def kill_decorate(kill):
    info = kill._asdict()
    info['killer_obj'] = s.get_player_fields(kill.killer, ['lastcountry'])
    info['victim_obj'] = s.get_player_fields(kill.victim, ['lastcountry'])
    return info

  data = {
      'next_url': url_for('latestkills', startat=startat + 20),
      'kills': map(kill_decorate, s.get_last_kills(startat)),
      'gunpic': gunpic,
      'fixdate': lambda x: datetime.utcfromtimestamp(int(x))
  }

  if startat >= 20:
    data['prev_url'] = url_for('latestkills', startat=startat - 20)
  else:
    data['prev_url'] = False

  return render_template('latestkills.html', **data)


@app.route('/players', defaults=dict(startat=0))
@app.route('/players/pos/<int:startat>')
def top_players(startat):
  s = stats()

  if (startat % 20):
    startat = 0

  data = {
      'next_url': url_for('top_players', startat=startat + 20),
      'players': s.get_top_killers(startat),
  }

  if startat >= 20:
    data['prev_url'] = url_for('top_players', startat=startat - 20)
  else:
    data['prev_url'] = False

  return render_template('players.html', **data)


@app.route('/weapons')
def weapons():
  s = stats()

  data = {
      'weapons': s.get_top_weapons(),
  }

  return render_template('weapons.html', **data)


@app.route('/')
def index():
  s = stats()
  return render_template('index.html', killsperdate=s.get_kills_for_date_range())


def main():
  app.run(host='0.0.0.0', debug=True)
