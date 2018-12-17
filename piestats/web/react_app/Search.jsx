import React, { Component} from "react";

import {fixdate, ErrorBar, CountryPic, PlayerLink} from "./Misc.jsx";

function PlayerResult(props) {
    return (
      <tr key={props.name}>
        <td><CountryPic country={props.lastcountry} /></td>
        <td><PlayerLink name={props.name} server={props.server} /></td>
        <td>{props.kills}</td>
        <td>{fixdate(props.firstseen)}</td>
        <td>{fixdate(props.lastseen)}</td>
      </tr>
      )
}

class Search extends React.Component {
  constructor(props) {
    super(props)
    this._mounted = false
    this.state = {
      loading: true,
      players: [],
      error: null,
      searcher: null
    }
  }
  getPlayers() {
    if (!this._mounted) {
        return
    }

    let player = null;
    for (let pair of this.props.location.search.slice(1).split('&')) {
      let parts = pair.split('=');
      if (parts.length == 2 && parts[0] == 'name' && parts[1].length) {
        try {
          player = decodeURIComponent(parts[1]);
        } catch (e) {
          console.log('Cannot decode URL ', parts[1], e)
          player = null;
        }
        break;
      }
    }

    if (!player) {
      if (this.state.loading) {
        this.setState((state, props) => {
          state.loading = false
          state.players = []
          state.error = 'No player specified'
          return state;
        })
      }
      return
    }

    if (this.state.searcher == player) {
      return
    }

    fetch("/v0/"+this.props.match.params.server+"/search?name=" + player)
      .then(res => res.json())
      .then(
        (result) => {
          if (!this._mounted) {
              return
          }
          this.setState((state, props) => {
            state.loading = false
            state.players = result.results
            state.error = result.error
            return state;
          })
        },
        (error) => {
          if (!this._mounted) {
              return
          }
          this.setState((state, props) => {
            state.loading = false
            state.players = []
            state.error = 'Failed loading'
            return state;
          })
        }
      )
  }
  componentDidMount() {
    this._mounted = true
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Search Results');
    this.getPlayers()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
    this.getPlayers()
  }
  componentWillUnmount() {
    this._mounted = false
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
    <div className="panel panel-default">
      <table className="table table-striped">
        <thead>
          <tr>
            <th colSpan="2">Player</th>
            <th>Kills</th>
            <th>Firstseen</th>
            <th>Lastseen</th>
          </tr>
        </thead>
        <tbody>
        {
          this.state.players.map((player) => {
            player.server = this.props.match.params.server;
            return PlayerResult(player);
          })
        }
        </tbody>
      </table>
    </div>
    )
  }
}

export default Search;
