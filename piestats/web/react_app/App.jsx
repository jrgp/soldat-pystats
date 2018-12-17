import React, { Component} from "react";
import "./App.css";

import Players from "./Players.jsx";
import Player from "./Player.jsx";
import Kills from "./Kills.jsx";
import Home from "./Home.jsx";
import Weapons from "./Weapons.jsx";
import Maps from "./Maps.jsx";
import Map from "./Map.jsx";
import Rounds from "./Rounds.jsx";
import Round from "./Round.jsx";
import Search from "./Search.jsx";

import {withRouter, BrowserRouter as Router, Route, Switch, Redirect, NavLink, Link } from "react-router-dom";

function getServerTitle(slug) {
  const server_obj = window.servers.find((s) => s.slug == slug);
  return server_obj ? server_obj.title : null;
}

function TopServerStat(props) {
  const server_obj = window.servers.find((s) => s.slug == props.server);
  if (!server_obj) {
    return '';
  }
  return (
      <p className="navbar-text pull-right">
         {server_obj.num_kills} kills by {server_obj.num_players} players since {window.since}
      </p>
  )
}

function topServerDropdownLink(slug, updateServer) {
  var helper = () => {
    updateServer(slug)
  }
  return (
    <li key={slug}>
      <Link onClick={helper} to={{
        pathname: "/"+slug,
        state: {
          server: slug
        }
      }}>{getServerTitle(slug)}</Link>
    </li>
  )
}

class PlayerSearchBox_ extends React.Component {
  constructor(props) {
    super(props)
    this.submitHandler = this.submitHandler.bind(this);
  }
  submitHandler(event) {
      event.preventDefault();
      var player = this.refs.player.value.trim();
      if (!player) {
        return;
      }
      this.props.history.push('/'+this.props.server+'/search?name='+encodeURIComponent(player))
  }
  render() {
    return (
        <form className="navbar-form navbar-left" role="search" method="get" onSubmit={this.submitHandler}>
          <div className="form-group">
            <input className="form-control input-sm" placeholder="Player search" type="text" ref="player" name="player" defaultValue="" />
          </div> <input type="submit" className="btn btn-default" value="Search!" />
        </form>
    )
  }
}

const PlayerSearchBox = withRouter(PlayerSearchBox_);

function TopServerNav(props) {
  return (
<nav className="navbar navbar-default navbar-fixed-top">
  <div className="container-fluid">
    <div className="navbar-header">
      <Link className="navbar-brand" to={"/"+props.server}>{getServerTitle(props.server)}</Link>
    </div>
    <div className="collapse navbar-collapse" id="top_nav_collapse">
      <TopServerStat server={props.server}/>
      <ul className="nav navbar-nav">
        <li className="dropdown">
          <a href="#" className="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">More Servers<span className="caret"></span></a>
          <ul className="dropdown-menu" role="menu">
          {
            window.servers.map((server) => topServerDropdownLink(server.slug, props.updateServer))
          }
          </ul>
        </li>
      </ul>
      <PlayerSearchBox server={props.server}/>
    </div>
  </div>
</nav>
  )
}

function NavBarLink({to, label}) {
  return (
     <Route exact path={to} activeOnlyWhenExact={true} children={({match}) => (
       <li className={match ? "active":""}><Link to={to}>{label}</Link></li>
     )}  />
  )
}

function NavBar(props) {
  return (
      <ul className="nav nav-tabs">
        <NavBarLink to={"/"+props.server} label="Overview" />
        <NavBarLink to={"/"+props.server+"/players"} label="Top Players" />
        <NavBarLink to={"/"+props.server+"/maps"} label="Top Maps" />
        <NavBarLink to={"/"+props.server+"/weapons"} label="Top Weapons" />
        <NavBarLink to={"/"+props.server+"/rounds"} label="Latest Rounds" />
        <NavBarLink to={"/"+props.server+"/kills"} label="Latest Kills" />
      </ul>
  )
}

class WrapperPage extends Component{
  constructor(props){
    super(props)
    this.state = {
      server: props.match.params.server,
      title: getServerTitle(props.match.params.server)
    };
    this.updateServer = this.updateServer.bind(this);
    this.updateTitle = this.updateTitle.bind(this);
  }
  updateServer(server) {
    if (this.state.server != server) {
      console.log('moving server to '+server)
      this.setState((state, props) => {
        state.server = server;
        return state;
      })
    }
  }
  updateTitle(title) {
    this.setState((state, props) => {
      state.title = title;
      return state;
    })
    document.title = title;
  }
  render() {
    const morerouteprops = {
      updateServer: this.updateServer,
      updateTitle: this.updateTitle
    };
    return(
<Router>
  <div className="container" id="mainContainer">
    <TopServerNav server={this.state.server} updateServer={this.updateServer} />
    <div className="page-header">
      <h1>{this.state.title}</h1>
      <NavBar server={this.state.server} />
    </div>
    <Switch>
      <Route exact strict path="/:server" render={props => {
          return <Home {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/players" render={props => {
          return <Players {...morerouteprops} {...props}/>;
        }
      } />
      <Route exact strict path="/:server/player/:player" render={props => {
          return <Player {...morerouteprops} {...props}/>;
        }
      } />
      <Route exact strict path="/:server/player" render={props => {
          return <Player {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/kills" render={props => {
          return <Kills {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/weapons" render={props => {
          return <Weapons {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/maps" render={props => {
          return <Maps {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/map/:map" render={props => {
          return <Map {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/rounds" render={props => {
          return <Rounds {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/round/:roundid" render={props => {
          return <Round {...morerouteprops} {...props}/>;
        }
      } />
      <Route path="/:server/search" render={props => {
          return <Search {...morerouteprops} {...props}/>;
        }
      } />
    </Switch>
    <footer>
      Generated by <a href="https://github.com/jrgp/soldat-pystats">Soldat Pystats</a> by Joe Gillotti.
      <span className="pull-right">Times in {window.timezone}.</span>
    </footer>
  </div>
</Router>
    );
  }
}

class App extends Component{
  render() {
    return(
<Router>
    <Switch>
      <Route path="/:server" component={WrapperPage} />
    </Switch>
</Router>
    );
  }
}

export default App;
