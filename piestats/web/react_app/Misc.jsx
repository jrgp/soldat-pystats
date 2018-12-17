import React, {Component} from "react";

import { Link } from "react-router-dom";

function fixdate(timestamp) {
  var d = new Date(timestamp * 1000);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
}

function CountryPic(props) {
  if (!props.country) {
    return '';
  }
  return <img width="16" height="11" src={"/static/flags/"+props.country.toLowerCase()+".png"} title={props.country} />
}

function PlayerLink(props) {
  if (!props.name) {
    return ''
  }
  if (props.name.match(/^[^.][a-zA-Z0-9-\. ]+$/)) {
    return <Link to={"/"+props.server+"/player/"+props.name}>{props.name}</Link>;
  } else {
    return <Link to={"/"+props.server+"/player?name="+encodeURIComponent(props.name)}>{props.name}</Link>;
  }
}

function MapLink(props) {
  return <Link to={"/"+props.server+"/map/"+props.name}>{props.name}</Link>;
}

function RoundLink(props) {
  if (!props.id) {
    return null;
  }
  return <Link to={"/"+props.server+"/round/"+props.id}>#{props.id}</Link>;
}

function WeaponPic(props) {
  if(props.weapon != 'Selfkill') {
    const url = '/static/soldatguns/' + props.weapon.replace(/ /g, '_') + '.png';
    return <img src={url} title={props.weapon} /> ;
  }
  return '';
}

function RoundOutcome(props) {
  var outcome = '';
  if (props.flagmatch) {
    if (props.winning_team) {
      const pretty_team = props.winning_team[0].toUpperCase() + props.winning_team.slice(1);
      outcome = (
        <span className={"team-"+props.winning_team}>{pretty_team} Won</span>
      );
    } else if (props.tie) {
      outcome = 'Tie';
    } else if (props.scores == 0) {
      outcome = 'No Scores';
    }
  } else if (props.winning_player) {
    outcome = (
      <span>
        <PlayerLink name={props.winning_player.name} server={props.server}/> Won
      </span>
    )
  }
  return outcome;
}

function ifnot0(value){
  return value ? value : 0;
}

function ErrorBar(props) {
  return (
  <div className="alert alert-dismissible alert-danger">
    {props.message}
  </div>
  )
}

export {fixdate, ifnot0, CountryPic, PlayerLink, WeaponPic, MapLink, RoundLink, RoundOutcome, ErrorBar};
