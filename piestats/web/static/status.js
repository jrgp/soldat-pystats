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

  $.get(url, function(data) {
    if (!data.success) {
      console.log('Failed: '+data.info);
      return;
    }

    var info = data.info;

    console.log('Got useful info')
    console.log(info)

    var template = Handlebars.compile([
      '<table class="table">',
        '<tbody>',
          '{{#each panel}}',
            '<tr>',
              '<th>{{@key}}</th>',
              '<td>{{this}}</td>',
            '</tr>',
          '{{/each}}',
          '<tr>',
            '<th>Join!</th>',
            '<td>{{# if country}}<img src="/static/flags/{{country}}.png"> {{/if}}<a href="soldat://{{ip}}:{{port}}">{{ip}}:{{port}}</a></td>',
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
            '</tr>',
          '</thead>',
          '<tbody>',
            '{{#each players}}',
              '<tr>',
              '<td>{{# if country}}<img src="/static/flags/{{country}}.png"> {{/if}}{{name}}</td>',
              '<td>{{team}}</td>',
              '<td>{{kills}}</td>',
              '<td>{{deaths}}</td>',
              '</tr>',
            '{{/each}}',
          '</tbody>',
        '</table>',
      '{{/if}}'
    ].join(''));

    for (var key in info.players) {
      info.players[key].team = team_names[info.players[key].team];
    }

    var context = {
      panel: {
        'Map': info.map,
        'Game mode': game_modes[info.mode],
        'Players': info.players.length,
        'Time left': Math.round(info.currentTime / 60) +' minutes'
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
