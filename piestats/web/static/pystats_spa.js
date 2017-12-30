function pystats_app() {
  var root = null;
  var useHash = true; // Defaults to: false
  var hash = '#'; // Defaults to: '#'
  var router = new Navigo(root, useHash, hash);
  var server = 'local';
  var $body = $('#body');
  var $title = $('h1');
  var $tab_bar = $('#tab-bar');

  Handlebars.registerHelper('notFalse', function(conditional, options) {
    if (conditional === false) {
      return options.inverse(this);
    }
    return options.fn(this);
  });

  Handlebars.registerHelper('playerShowCountry', function(conditional, options) {
    var name = typeof(conditional) == 'string' ? conditional : conditional.name;
    if (name.toLowerCase().indexOf('major') === 0) {
      return options.inverse(this);
    }
    return options.fn(this);
  });

  Handlebars.registerHelper('lowerStr', function(str) {
    return str.toLowerCase();
  });

  Handlebars.registerHelper('defaultZero', function(value) {
    return value ? value : 0;
  });

  Handlebars.registerHelper('weaponFilename', function(weapon) {
    if (typeof(weapon) == 'string') {
      return weapon.replace(' ', '_') + '.png';
    } else {
      return weapon[0].replace(' ', '_') + '.png';
    }
  });

  var players_template = Handlebars.compile($('#players_template').html());
  var players_profile_template = Handlebars.compile($('#players_profile_template').html());
  var weapons_template = Handlebars.compile($('#weapons_template').html());
  var kills_template = Handlebars.compile($('#kills_template').html());

  function finalizePageRender(activeTab, title) {
    $title.text(title);
    $tab_bar.find('li').removeClass('active');
    if (activeTab) {
      $tab_bar.find('a[href="'+activeTab+'"]').parent().addClass('active');
    }
    router.updatePageLinks()
  }

  function renderPlayersList(params) {
    var startat = params ? params.pos : false;
    $.get('/v0/' + server + '/players' + (startat ? '/pos/' + startat : ''), function(data) {
      data.players = data.players.map(function(p) {return p.info;});
      $body.html(players_template(data));
      finalizePageRender('players', 'Top Players');
    });
  }

  function renderKillsList(params) {
    var startat = params ? params.pos : false;
    $.get('/v0/' + server + '/kills' + (startat ? '/pos/' + startat : ''), function(data) {
      $body.html(kills_template(data));
      finalizePageRender('kills', 'Latest Kills');
    });
  }

  function renderWeaponsPage() {
    $.get('/v0/' + server + '/weapons', function(data) {
      $body.html(weapons_template(data));
      finalizePageRender('weapons', 'Top Weapons');
    });
  }

  function renderOverviewPage() {
    $body.html('');
    finalizePageRender('/', 'Stats Overview');
  }

  function renderPlayersProfile(params) {
    var player = params.player;
    $.get('/v0/' + server + '/player/' + player, function(data) {
      $body.html(players_profile_template(data));
      finalizePageRender('players', decodeURI(player));
    });
  }

  router.on({
    '/kills/pos/:pos': renderKillsList,
    '/players/pos/:pos': renderPlayersList,
    '/player/:player': renderPlayersProfile,
    '/players': renderPlayersList,
    '/weapons': renderWeaponsPage,
    '/kills': renderKillsList,
    '/': renderOverviewPage,
  }).resolve();
}
