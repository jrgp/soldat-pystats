function load_server_status(url, elem) {
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

  elem.html('<p style="text-align: center; margin: 10px;">Loading..</p>');

  $.get(url, function(data) {
    if (!data.success) {
      console.log('Failed: '+data.info);
      elem.empty()
      elem.append($('<p style="text-align: center; margin: 10px;">').text(data.info));
      return;
    }

    var info = data.info;

    var template = Handlebars.compile([
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

      '{{# if players_count}}',
        '<table class="table table-striped">',
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
              '<td>{{# if country}}<img title="{{country}}" src="/static/flags/{{country}}.png"> {{/if}}<a href="{{{url}}}">{{name}}</a></td>',
              '<td>{{team}}</td>',
              '<td>{{kills}}</td>',
              '<td>{{deaths}}</td>',
              '<td>{{ping}}</td>',
              '</tr>',
            '{{/each}}',
          '</tbody>',
        '</table>',
      '{{/if}}'
    ].join(''));

    for (var key in info.players) {
      info.players[key].team = team_names[info.players[key].team];
      info.players[key].url = '/'+info['server_slug']+'/search?player='+encodeURIComponent(info.players[key].name);
    }

    var context = {
      panel: {
        'Map': info.map,
        'Game mode': game_modes[info.mode],
        'Players': info.players.length,
        'Time left': info.minutesLeft + ' minutes'
      },
      players: info.players,
      ip: info.ip,
      country: info.country,
      port: info.port,
      players_count: info.players.length
    };

    elem.html(template(context));

  });
}
