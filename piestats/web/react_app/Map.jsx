import React, { Component} from "react";

import {WeaponPic, MapLink, ErrorBar} from "./Misc.jsx";

function WeaponRow(props) {
  return (
    <tr key={props.name}>
      <td width="10" className="alignright"><WeaponPic weapon={props.name} /></td>
      <td>{props.name}</td>
      <td>{props.kills}</td>
    </tr>
  )
}

class Map extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      info: null,
      error: null
    }
  }
  getMap(pos) {
    fetch("/v0/"+this.props.match.params.server+"/map/"+this.props.match.params.map)
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
    this.props.updateTitle('Map '+this.props.match.params.map);
    this.getMap()
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
    var scores = null;
    if (this.state.info.flags) {
      scores = (
         <>
          <tr>
            <th>Scores</th>
            <td>
              <span>
                <span className="team-alpha">{this.state.info.scores_alpha}</span> <span className="team-bravo">{this.state.info.scores_bravo}</span>
              </span>
            </td>
          </tr>
          <tr>
            <th>Wins</th>
            <td>
              <span>
                <span className="team-alpha">{this.state.info.wins_alpha}</span> <span className="team-bravo">{this.state.info.wins_bravo}</span>
              </span>
            </td>
          </tr>
          <tr>
            <th>Ties</th>
            <td>{this.state.info.ties}</td>
          </tr>
         </>
      )
    }

    var svg = null;
    if (this.state.info.svg_exists) {
      const svg_url = "/v0/"+this.props.match.params.server+"/map/"+this.props.match.params.map+"/svg";
      svg = (
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">Wireframe Polygons</h3>
            </div>
            <a href={svg_url}>
              <img className="mapsvg" src={svg_url}
                   title={"Polygons for "+this.state.info.name}
                   alt={"Polygons for "+this.state.info.name} />
            </a>
          </div>
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
                  <th>Name</th>
                  <td>{this.state.info.name}</td>
                </tr>
                <tr>
                  <th>Plays</th>
                  <td>{this.state.info.plays}</td>
                </tr>
                <tr>
                  <th>Kills</th>
                  <td>{this.state.info.kills}</td>
                </tr>
                {scores ? scores : null}
              </tbody>
            </table>
          </div>
          {svg ? svg : null}
        </div>

        <div className="col-xs-12  col-md-6">
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
                    Object.keys(this.state.info.weapons)
                      .map(key => this.state.info.weapons[key])
                      .sort((a, b) => b.kills - a.kills)
                      .map(weapon => WeaponRow(weapon))
                  }
               </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }
}

export default Map;
