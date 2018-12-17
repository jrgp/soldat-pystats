import React, { Component} from "react";
import Pager from "./Pager.jsx";

import {WeaponPic} from "./Misc.jsx";

function Weapon(props) {
    return (
      <tr key={props.name}>
        <td width="10" className="alignright "><WeaponPic weapon={props.name} /></td>
        <td>{props.name}</td>
        <td>{props.kills}</td>
      </tr>
      )
}

class Weapons extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      weapons: []
    }
  }
  getWeapons(pos) {
    fetch("/v0/"+this.props.match.params.server+"/weapons")
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            weapons: result.data,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Top Weapons');
    this.getWeapons()
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
    return (
    <div>
    <div className="panel panel-default">
      <table className="table table-striped">
        <thead>
          <tr>
            <th colSpan="2">Weapon</th>
            <th>Kills</th>
          </tr>
        </thead>
        <tbody>
        {
          this.state.weapons.map((weapon) => Weapon(weapon))
        }
        </tbody>
      </table>
    </div>
    </div>
    )
  }
}

export default Weapons;
