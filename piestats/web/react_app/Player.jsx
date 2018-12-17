import React, { Component} from "react";
import {fixdate, ifnot0, WeaponPic, CountryPic, MapLink, PlayerLink, ErrorBar} from "./Misc.jsx";

function WeaponRow(props) {
  return (
    <tr key={props.name}>
      <td width="10" className="alignright"><WeaponPic weapon={props.name} /></td>
      <td>{props.name}</td>
      <td>{ifnot0(props.kills)}</td>
      <td>{ifnot0(props.deaths)}</td>
    </tr>
  )
}

function MapRow(props) {
  return (
      <tr key={props.name}>
        <td><MapLink name={props.name} server={props.server}/></td>
        <td>{ifnot0(props.kills)}</td>
        <td>{ifnot0(props.deaths)}</td>
        <td>{ifnot0(props.suicides)}</td>
        <td>
          <span className="team-alpha">{ifnot0(props.scores_alpha)}</span> <span className="team-bravo">{ifnot0(props.scores_alpha)}</span>
        </td>
      </tr>
  )
}

function TopRivalRow(props){
  return (
    <tr key={props.name}>
        <td className="nowidth"><CountryPic country={props.lastcountry} /></td>
        <td><PlayerLink name={props.name} server={props.server}/></td>
        <td>{props.info.kills}</td>
        <td>{props.info.kd}</td>
    </tr>
  )
}

class Player extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      info: null,
      error: null,
      player: ''
    }
  }
  getPlayer() {

    // Depending on how funky the player name is, either keep it in the query string or the url path
    let url = null;
    let player = null;
    if (this.props.match.params.player) {
      url = "/v0/"+this.props.match.params.server+"/player/"+this.props.match.params.player;
      player = this.props.match.params.player;
    } else {
      for (let pair of this.props.location.search.slice(1).split('&')) {
        let parts = pair.split('=');
        if (parts.length == 2 && parts[0] == 'name' && parts[1].length) {
          player = decodeURIComponent(parts[1]);
          url = "/v0/"+this.props.match.params.server+"/player?name="+parts[1];
          break;
        }
      }
    }

    if (!player) {
      this.setState((state, props) => {
        state.error = 'URL Missing player name';
        return state;
      });
      return;
    }

    if (player == this.state.player) {
      return;
    }

    if (this.state.player != player) {
        this.setState((state, props) => {
          state.player = player;
          return state;
        });
    }

    fetch(url)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState((state, props) => {
            state.loading = false
            state.info = result.data
            state.error = result.error
            this.props.updateTitle(this.state.player);
            return state;
          })
        },
        (error) => {
          this.setState((state, props) => {
            state.loading = false
            state.error = 'Failed loading'
            this.props.updateTitle('Error');
            return state;
          })
        }
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.getPlayer()
  }
  componentWillUpdate(){
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
    this.getPlayer()
  }
  render() {
    if (this.state.loading) {
      return (
        <span>Loading..</span>
      )
    }
    if (this.state.error) {
      return (
        <ErrorBar message={this.state.error} />
      )
    }
    let country = null
    if (this.state.info.player.lastcountry) {
      country = (
        <>
          <tr>
            <th>Country</th>
            <td>
              <CountryPic country={this.state.info.player.lastcountry} />
            </td>
          </tr>
        </>
      )
    }
    return (
      <div className="row" key={this.props.match.params.player}>
        <div className="col-xs-12  col-md-6">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Overview</h3>
            </div>
            <table className="table table-striped">
              <tbody>
                <tr></tr>
                <tr>
                  <th>Name</th>
                  <td>{this.state.info.player.name}</td>
                </tr>
                <tr>
                  <th>Kills</th>
                  <td>{this.state.info.player.kills}</td>
                </tr>
                <tr>
                  <th>Deaths</th>
                  <td>{this.state.info.player.deaths}</td>
                </tr>
                <tr>
                  <th>Scores</th>
                  <td>
                    <span className="team-alpha">{this.state.info.player.scores_alpha}</span> <span className="team-bravo">{this.state.info.player.scores_bravo}</span>
                  </td>
                </tr>
                <tr>
                  <th>First Seen</th>
                  <td>{fixdate(this.state.info.player.firstseen)}</td>
                </tr>
                <tr>
                  <th>Last Seen</th>
                  <td>{fixdate(this.state.info.player.lastseen)}</td>
                </tr>
                {country}
                <tr>
                  <th>Known names</th>
                  <td>{this.state.info.player.names.join(', ')}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Weapons</h3>
            </div>
            <table className="table table-striped">
              <thead>
                <tr>
                  <th colSpan="2" className="alignleft">Wep</th>
                  <th>Kills</th>
                  <th>Deaths</th>
                </tr>
               </thead>
               <tbody>
                {
                  Object.keys(this.state.info.player.weapons)
                    .map(key => this.state.info.player.weapons[key])
                    .sort((a, b) => b.kills - a.kills)
                    .map(weapon => WeaponRow(weapon))
                }
               </tbody>
            </table>
          </div>
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Favorite Maps</h3>
            </div>
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>Map</th>
                  <th>Kills</th>
                  <th>Deaths</th>
                  <th>Suicides</th>
                  <th>Scores</th>
                </tr>
               </thead>
               <tbody>
                {
                  Object.keys(this.state.info.player.maps)
                    .map(key => this.state.info.player.maps[key])
                    .sort((a, b) => b.kills - a.kills)
                    .map(map => {
                      map.server = this.props.match.params.server;
                      return MapRow(map)
                    })
                }
               </tbody>
            </table>
          </div>
        </div>

        <div className="col-xs-12  col-md-6">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Top Victims</h3>
            </div>
            <table className="table table-striped">
              <thead>
                <tr>
                  <th colSpan="2">Player</th>
                  <th>Kills</th>
                  <th>K:D</th>
                </tr>
               </thead>
               <tbody>
                {
                  this.state.info.top_victims.map(rival => {
                    rival.server = this.props.match.params.server;
                    return TopRivalRow(rival, this.updatePlayer)
                  })
                }
               </tbody>
            </table>
          </div>
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Top Enemies</h3>
            </div>
            <table className="table table-striped">
              <thead>
                <tr>
                  <th colSpan="2">Player</th>
                  <th>Deaths</th>
                  <th>K:D</th>
                </tr>
               </thead>
               <tbody>
                {
                  this.state.info.top_enemies.map(rival => {
                    rival.server = this.props.match.params.server;
                    return TopRivalRow(rival)
                  })
                }
               </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }
}

export default Player;
