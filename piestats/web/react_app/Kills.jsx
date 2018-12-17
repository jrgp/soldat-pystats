import React, {Component} from "react";
import Pager from "./Pager.jsx";
import {fixdate, RoundLink, CountryPic, PlayerLink, WeaponPic} from "./Misc.jsx";


function Kill(props) {
    return (
            <tr key={props._id}>
              <td className="nowidth"><CountryPic country={props.killer_obj.lastcountry} /></td>
              <td><PlayerLink server={props.server} name={props.killer_obj.name} /></td>
              <td className="nowidth"><CountryPic country={props.victim_obj.lastcountry} /></td>
              <td><PlayerLink server={props.server} name={props.victim_obj.name} /></td>
              <td className="nowidth alignright"><WeaponPic weapon={props.weapon}/></td>
              <td>{props.weapon}</td>
              <td>{fixdate(props.datetime)}</td>
              <td><RoundLink id={props.round_id} server={props.server}/></td>
            </tr>
      )
}

class Kills extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      maxitems: null,
      kills: []
    }
    this.onPagerChange = this.onPagerChange.bind(this);
  }
  getKills(pos) {
    if (!this.state.loading) {
        this.setState((state, props) => {
          state.loading = true
          return state
        })
    }
    fetch("/v0/"+this.props.match.params.server+"/kills" + (pos ? "/pos/" + pos : ""))
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            kills: result.data,
            maxitems: result.total_items,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount() {
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Latest Kills');
    this.getKills()
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
  }
  onPagerChange(newpos) {
    this.getKills(newpos)
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
              <th colSpan="2">Killer</th>
              <th colSpan="2">Victim</th>
              <th colSpan="2">Weapon</th>
              <th>When</th>
              <th>Round</th>
            </tr>
          </thead>
          <tbody>
          {
            this.state.kills.map((kill) => {
              kill.server = this.props.match.params.server;
              return Kill(kill)
            })
          }
          </tbody>
        </table>
      </div>
    </div>
    )
  }
}

export default Kills;
