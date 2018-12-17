import React, { Component} from "react";

import {fixdate, ErrorBar, WeaponPic, CountryPic, MapLink, PlayerLink, RoundOutcome} from "./Misc.jsx";

function WeaponRow(props) {
  return (
    <tr key={props.name}>
      <td width="10" className="alignright"><WeaponPic weapon={props.name} /></td>
      <td>{props.name}</td>
      <td>{props.kills}</td>
    </tr>
  )
}

function PlayerRow(props) {
  return (
      <tr key={props.name}>
        <td className="nowidth"><CountryPic country={props.obj.lastcountry} /></td>
        <td><PlayerLink name={props.name} server={props.server}/></td>
        <td>{props.kills}</td>
        <td>{props.deaths}</td>
        <td>
          <span className="team-alpha">{ props.obj.scores_alpha }</span> <span className="team-bravo">{ props.obj.scores_bravo }</span>
        </td>
      </tr>
  )
}

class Round extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      info: null,
      error: null
    }
  }
  getround(pos) {
    fetch("/v0/"+this.props.match.params.server+"/round/"+this.props.match.params.roundid)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            info: result.data,
            error: result.error,
            loading: false
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
    this.props.updateTitle('Round '+this.props.match.params.roundid);
    this.getround()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
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
    return (
<div className="row">
  <div className="col-xs-12  col-md-6">
    <div className="panel panel-default">
      <div className="panel-heading">
        <h3 className="panel-title">Overview</h3>
      </div>
      <table className="table table-striped">
        <tbody>
          <tr></tr>
          <tr>
            <th>Started</th>
            <td>{fixdate(this.state.info.round.started)}</td>
          </tr>
          <tr>
            <th>Duration</th>
            <td>{this.state.info.round.pretty_duration}</td>
          </tr>
          <tr>
            <th>Map</th>
            <td><MapLink name={this.state.info.round.map} server={this.props.match.params.server}/></td>
          </tr>
          <tr>
            <th>Kills</th>
            <td>{this.state.info.round.kills}</td>
          </tr>

          <tr>
            <th>Outcome</th>
            <td>
                <RoundOutcome server={this.props.match.params.server} {...this.state.info.round}/>
            </td>
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
          </tr>
         </thead>
         <tbody>
            {
              Object.keys(this.state.info.round.weapons)
                .map(key => this.state.info.round.weapons[key])
                .sort((a, b) => b.kills - a.kills)
                .map(weapon => WeaponRow(weapon))
            }
         </tbody>
      </table>
    </div>
  </div>

  <div className="col-xs-12  col-md-6">
    <div className="panel panel-default">
      <div className="panel-heading">
        <h3 className="panel-title">Players</h3>
      </div>
      <table className="table table-striped">
        <thead>
          <tr>
            <th colSpan="2">Player</th>
            <th>Kills</th>
            <th>Deaths</th>
            <th>Scores</th>
          </tr>
         </thead>
         <tbody>
            {
              Object.keys(this.state.info.players)
                .map(key => this.state.info.players[key])
                .sort((a, b) => b.kills - a.kills)
                .map(player => {
                  player.server = this.props.match.params.server;
                  return PlayerRow(player);
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

export default Round;
