import React, { Component} from "react";
import Pager from "./Pager.jsx";

import {fixdate, RoundLink, MapLink, RoundOutcome} from "./Misc.jsx";

function Round(props) {
    var scores = '-', outcome = '-';
    if (props.flags) {
      scores =  (
          <span>
            <span className="team-alpha">{props.alpha_scores}</span> <span className="team-bravo">{props.bravo_scores}</span>
          </span>
      );
    }
    return (
      <tr key={props.id}>
        <td><RoundLink id={props.id} server={props.server}/></td>
        <td>{fixdate(props.started)}</td>
        <td>{props.pretty_duration}</td>
        <td><MapLink name={props.map} server={props.server}/></td>
        <td>{props.num_players}</td>
        <td>{props.kills}</td>
        <td>{scores}</td>
        <td><RoundOutcome {...props}/></td>
      </tr>
      )
}

class Rounds extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      maxitems: null,
      rounds: []
    }
    this.onPagerChange = this.onPagerChange.bind(this);
  }
  getrounds(pos) {
    fetch("/v0/"+this.props.match.params.server+"/rounds" + (pos ? "/pos/" + pos : ""))
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            rounds: result.data,
            maxitems: result.total_items,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Latest Rounds');
    this.getrounds()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
  }
  onPagerChange(newpos) {
    this.getrounds(newpos)
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
            <th>#</th>
            <th>When</th>
            <th>Duration</th>
            <th>Map</th>
            <th># Players</th>
            <th>Kills</th>
            <th>Scores</th>
            <th>Outcome</th>
          </tr>
        </thead>
        <tbody>
        {
          this.state.rounds.map((round) => {
            round.server = this.props.match.params.server;
            return Round(round);
          })
        }
        </tbody>
      </table>
    </div>
    </div>
    )
  }
}

export default Rounds;
