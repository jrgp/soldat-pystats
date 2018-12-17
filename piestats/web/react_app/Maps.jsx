import React, { Component} from "react";
import Pager from "./Pager.jsx";

import {fixdate, CountryPic, MapLink} from "./Misc.jsx";

function Map(props) {
    var scores = '-', wins = '-';
    if (props.flags) {
      scores =  (
          <span>
            <span className="team-alpha">{props.scores_alpha}</span> <span className="team-bravo">{props.scores_bravo}</span>
          </span>
      );
      wins = (
          <span>
            <span className="team-alpha">{props.wins_alpha}</span> <span className="team-bravo">{props.wins_bravo}</span>
          </span>
      );
    }

    return (
      <tr key={props.name}>
        <td><MapLink name={props.name} server={props.server}/></td>
        <td>{props.plays}</td>
        <td>{props.kills}</td>
        <td>{scores}</td>
        <td>{wins}</td>
      </tr>
      )
}

class Maps extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      maxitems: null,
      maps: []
    }
    this.onPagerChange = this.onPagerChange.bind(this);
  }
  getMaps(pos) {
    fetch("/v0/"+this.props.match.params.server+"/maps" + (pos ? "/pos/" + pos : ""))
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            maps: result.data,
            maxitems: result.total_items,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Top Maps');
    this.getMaps()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
  }
  onPagerChange(newpos) {
    this.getMaps(newpos)
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
            <th>Map</th>
            <th>Plays</th>
            <th>Kills</th>
            <th>Scores</th>
            <th>Wins</th>
          </tr>
        </thead>
        <tbody>
        {
          this.state.maps.map((map) => {
            map.server = this.props.match.params.server;
            return Map(map);
          })
        }
        </tbody>
      </table>
    </div>
    </div>
    )
  }
}

export default Maps;

