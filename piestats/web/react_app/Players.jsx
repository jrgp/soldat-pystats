import React, { Component} from "react";
import Pager from "./Pager.jsx";

import {fixdate, CountryPic, PlayerLink} from "./Misc.jsx";

function Player(props) {
    return (
      <tr key={props.name}>
        <td><CountryPic country={props.lastcountry} /></td>
        <td><PlayerLink name={props.name} server={props.server} /></td>
        <td>{props.kills}</td>
        <td>{props.deaths}</td>
        <td>
          <span className="team-alpha">{ props.scores_alpha }</span> <span className="team-bravo">{ props.scores_bravo }</span>
        </td>
        <td>{fixdate(props.firstseen)}</td>
        <td>{fixdate(props.lastseen)}</td>
      </tr>
      )
}

class Players extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      maxitems: null,
      players: []
    }
    this.onPagerChange = this.onPagerChange.bind(this);
  }
  getPlayers(pos) {
    fetch("/v0/"+this.props.match.params.server+"/players" + (pos ? "/pos/" + pos : ""))
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            players: result.data,
            maxitems: result.total_items,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Top Players');
    this.getPlayers()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
  }
  onPagerChange(newpos) {
    this.getPlayers(newpos)
  }
  render() {
    if (this.state.loading) {
      return (
        <span>Loading..</span>
      )
    }
    return (
    <div>
      <Pager incr={20} onPagerChange={this.onPagerChange} maxitems={this.state.maxitems} />
    <div className="panel panel-default">
      <table className="table table-striped">
        <thead>
          <tr>
            <th colSpan="2">Player</th>
            <th>Kills</th>
            <th>Deaths</th>
            <th>Scores</th>
            <th>Firstseen</th>
            <th>Lastseen</th>
          </tr>
        </thead>
        <tbody>
        {
          this.state.players.map((player) => {
            player.server = this.props.match.params.server;
            return Player(player);
          })
        }
        </tbody>
      </table>
    </div>
    </div>
    )
  }
}

export default Players;
