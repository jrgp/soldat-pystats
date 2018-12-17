import React, { Component} from "react";
import {CountryPic, PlayerLink, MapLink} from "./Misc.jsx";

const game_modes = [
  'Deathmatch',
  'Pointmatch',
  'Team Deathmatch',
  'Capture the Flag',
  'Rambomatch',
  'Infiltration',
  'Hold the Flag'
];
const team_names = [
  'none',
  'alpha',
  'bravo',
  'charlie',
  'delta',
  'spectator'
];

function CoreRow(props) {
  return (
      <tr>
        <th>{props.k}</th>
        <td>{props.value}</td>
      </tr>
  )
}

function PlayerRow(props) {
  return (
      <tr key={props.name}>
        <td>
          {props.country ? <CountryPic country={props.country} /> : null}
          <PlayerLink name={props.name} server={props.server} />
         </td>
        <td><span className={'team-'+team_names[props.team]}>{team_names[props.team]}</span></td>
        <td>{props.kills}</td>
        <td>{props.deaths}</td>
        <td>{props.bot ? <img title="Bot" src="/static/bot.png" /> : props.ping}</td>
      </tr>
  )
}

class ServerStatus extends React.Component {
  constructor(props) {
    super(props)
    this._mounted = false
    this.state = {
      loading: true,
      info: null,
      error: null,
      server: null
    }
  }
  loadStatus(){
    if (!this._mounted) {
        return
    }

    if (this.state.server == this.props.server) {
      return
    }

    fetch('/v0/'+this.props.server+'/status')
      .then(res => res.json())
      .then(
        (result) => {
          if (!this._mounted) {
              return
          }
          this.setState((state, props) => {
            state.loading = false
            state.info = result.info;
            state.error = result.error;
            state.server = this.props.server;
            return state;
          })
        },
        (error) => {
          if (!this._mounted) {
              return
          }
          this.setState((state, props) => {
            state.loading = false
            state.error = 'Failed hitting'
            state.server = this.props.server;
            return state;
          })
        }
      )
  }
  componentDidMount(){
    this._mounted = true
    this.loadStatus()
  }
  componentDidUpdate(){
    this.loadStatus()
  }
  componentWillUnmount() {
    this._mounted = false
  }
  render(){
    if (this.state.loading) {
      return null;
    }

    if (this.state.error) {
      return (
        <div className="row">
          <div className="col-xs-12 col-md-6">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h3 className="panel-title">Current Server Status</h3>
              </div>
              <div id="server_status_core">
                <p>Failed loading stats: {this.state.error}</p>
              </div>
            </div>
          </div>
        </div>
      )
    }

    if (!this.state.info) {
      return null
    }

    const core_info = {
        Map: <MapLink name={this.state.info.map} server={this.props.server} />,
        'Game mode': game_modes[this.state.info.mode],
        Players: this.state.info.players.length + (this.state.info.botCount > 0 ? ' ('+this.state.info.botCount+' bots)' : ''),
        'Time left': this.state.info.minutesLeft + ' minutes'
    }

    return (
      <>
        <div className="row">
          <div className="col-xs-12 col-md-6">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h3 className="panel-title">Current Server Status</h3>
              </div>
              <div id="server_status_core">
                <table className="table table-striped" style={{marginBottom: 0}}>
                  <tbody>
                    {Object.keys(core_info).map((key) =>
                      <CoreRow key={key} k={key} value={core_info[key]} />
                    )}
                    <tr key="join">
                      <th>Join!</th>
                      <td>
                          {this.state.info.country ? <CountryPic country={this.state.info.country} /> : null}
                          <a href={"soldat://"+this.state.info.ip+":"+this.state.info.port}>{this.state.info.ip}:{this.state.info.port}</a>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div className="row" id="server_status_players_box">
          <div className="col-xs-12 col-md-6">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h3 className="panel-title">Current Server Players</h3>
              </div>
              <div id="server_status_players">
                <table className="table table-striped" style={{marginBottom: 0}}>
                  <thead>
                    <tr>
                    <th>Player Name</th>
                    <th>Team</th>
                    <th>Kills</th>
                    <th>Deaths</th>
                    <th>Ping</th>
                    </tr>
                  </thead>
                  <tbody>
                    {this.state.info.players.map((player) => {
                      player.server = this.props.server;
                      return PlayerRow(player);
                    })}
                  </tbody>
                </table>

              </div>
            </div>
          </div>
        </div>
      </>
    )
  }
}

export default ServerStatus;
