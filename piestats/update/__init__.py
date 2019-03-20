import pkg_resources

from piestats.update.parseevents import ParseEvents
from piestats.update.multiprocapplyevents import MultiProcApplyEvents
from piestats.update.roundmanager import RoundManager
from piestats.update.decorateevents import decorate_events
from piestats.update.hwid import Hwid

import geoip2.database


def update_events(r, keys, retention, filemanager, server, verbose):

  # Get raw events out of logs
  parse = ParseEvents(retention, filemanager, r, keys)

  # Manager of HWID <-> Name mappings
  hwid = Hwid(r, keys, verbose)

  # GeoIP lookups
  try:
    geoip_obj = geoip2.database.Reader(pkg_resources.resource_filename('piestats.update', 'GeoLite2-Country.mmdb'))
  except Exception as e:
    print 'Failed loading geoip file %s' % e

  # Connect to ftp/ssh or no-op if getting local files
  with filemanager.initialize():

    # Apply events with this
    with MultiProcApplyEvents(r=r, keys=keys, hwid=hwid, geoip=geoip_obj) as apply_events:

      # Need to get these
      map_titles, flag_score_maps = parse.build_map_names()

      # Maintain round state with this
      round_manager = RoundManager(r=r, keys=keys, flag_score_maps=flag_score_maps)

      # Maybe the last round is empty. Delete it if so
      round_manager.tweak_last_round()

      for logfile, events in parse.get_events():
        for decorated_event in decorate_events(events,
                                               map_titles=map_titles,
                                               ignore_maps=server.ignore_maps,
                                               ignore_players=server.ignore_players,
                                               round_manager=round_manager,
                                               logfile=logfile):
          apply_events.apply(decorated_event)
