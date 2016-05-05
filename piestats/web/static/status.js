function load_server_status(url) {
  var game_modes = [
    'Deathmatch',
    'Pointmatch',
    'Team Deathmatch',
    'Capture the Flag',
    'Rambomatch',
    'Infiltration',
    'Hold the Flag'
  ];
  var team_names = [
    'None',
    'Alpha',
    'Bravo',
    'Charlie',
    'Delta',
    'Spectator'
  ];
  var team_colors = [
    'darkgray',
    'red',
    'blue',
    'yellow',
    'green',
    'gray'
  ];

  var core_elem = $('#server_status_core');
  var players_elem = $('#server_status_players');
  var players_box = $('#server_status_players_box');

  core_elem.html('<p style="text-align: center; margin: 10px;">Loading..</p>');
  players_elem.html('<p style="text-align: center; margin: 10px;">Loading..</p>');

  $.get(url, function(data) {
    if (!data.success) {
      console.log('Failed: '+data.info);
      core_elem.empty()
      players_elem.empty()
      core_elem.append($('<p style="text-align: center; margin: 10px;">').text(data.info));
      players_box.hide();
      return;
    }

    var info = data.info;

    var core_template = Handlebars.compile([
      '<table class="table table-striped" style="margin-bottom: 0;">',
        '<tbody>',
          '{{#each panel}}',
            '<tr>',
              '<th>{{@key}}</th>',
              '<td>{{this}}</td>',
            '</tr>',
          '{{/each}}',
          '<tr>',
            '<th>Join!</th>',
            '<td>{{# if country}}<img title="{{country}}" src="/static/flags/{{country}}.png"> {{/if}}<a href="soldat://{{ip}}:{{port}}">{{ip}}:{{port}}</a></td>',
          '</tr>',
        '</tbody>',
      '</table>',
    ].join(''));

    var players_template = Handlebars.compile([
      '<table class="table table-striped" style="margin-bottom: 0;">',
        '<thead>',
          '<tr>',
          '<th>Player Name</th>',
          '<th>Team</th>',
          '<th>Kills</th>',
          '<th>Deaths</th>',
          '<th>Ping</th>',
          '</tr>',
        '</thead>',
        '<tbody>',
          '{{#each players}}',
            '<tr>',
            '<td>',
              '{{# if country}}<img title="{{country}}" src="/static/flags/{{country}}.png"> {{/if}}',
              '<a href="{{{url}}}">{{name}}</a>',
             '</td>',
            '<td>{{team}}</td>',
            '<td>{{kills}}</td>',
            '<td>{{deaths}}</td>',
            '<td>{{# if bot}}<img title="Bot" src="/static/bot.png">{{else}} {{ping}} {{/if}}</td>',
            '</tr>',
          '{{/each}}',
        '</tbody>',
      '</table>',
    ].join(''));

    for (var key in info.players) {
      info.players[key].team = team_names[info.players[key].team];
      info.players[key].url = '/'+info['server_slug']+'/search?player='+encodeURIComponent(info.players[key].name);
    }

    var core_context = {
      panel: {
        'Map': info.map,
        'Game mode': game_modes[info.mode],
        'Players': info.players.length + (info.botCount > 0 ? ' ('+info.botCount+' bots)' : ''),
        'Time left': info.minutesLeft + ' minutes'
      },
      ip: info.ip,
      country: info.country,
      port: info.port,
      players_count: info.players.length,
    };

    var players_context = {
      players: info.players
    };

    core_elem.html(core_template(core_context));

    if (info.players.length) {
      players_elem.html(players_template(players_context));
      players_box.show();
    }
    else {
      players_box.hide();
    }
  });
}
