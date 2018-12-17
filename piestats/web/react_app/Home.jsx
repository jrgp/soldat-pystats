import React, { Component} from "react";
import ServerStatus from "./Status.jsx";
import {ErrorBar} from "./Misc.jsx";
import {Line as BarChart, Pie as PieChart} from "react-chartjs";


function KillsChart(props){
  const chartData = {
    labels: props.killsperdate.map((info) => info[0]),
    datasets: [
      {
        label: 'Kills per day',
        fillColor: 'rgba(220,220,220,0.2)',
        strokeColor: 'rgba(220,220,220,1)',
        pointColor: 'rgba(220,220,220,1)',
        pointStrokeColor: '#fff',
        pointHighlightFill: '#fff',
        pointHighlightStroke: 'rgba(220,220,220,1)',
        data: props.killsperdate.map((info) => info[1])
      }
    ]
  };
  const chartOptions = {responsive: true};
  return (
      <BarChart data={chartData} options={chartOptions} height="200" />
  )
}

function CountryChart (props) {
    const chartData = props.topcountries;
    const chartOptions = {responsive: true, animation: false};
    return (
      <PieChart data={chartData} options={chartOptions} height="200" />
    )
}

class Home extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: true,
      info: null,
      server: null,
      error: null
    }
  }
  getServer() {
    const server = this.props.match.params.server;
    if (server == this.state.server) {
      return;
    }
    if (this.state.server != server) {
        this.setState((state, props) => {
          state.server = server;
          return state;
        });
    }
    fetch("/v0/"+server)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            info: result.data,
            error: result.error,
            loading: false
          })
        },
        (error) => {}
      )
  }
  componentDidMount(){
    this.props.updateServer(this.props.match.params.server)
    this.props.updateTitle('Stats Overview')
    this.getServer();
  }
  componentDidUpdate(){
    this.props.updateServer(this.props.match.params.server)
    this.getServer();
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
      <div>
        <div className="row">
          <div className="col-xs-12 col-md-6">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h3 className="panel-title">Kills this week</h3>
              </div>
              <div className="panel-body aligncenter" id="chart_latest_kills_parent">
                <KillsChart killsperdate={this.state.info.killsperdate} server={this.props.match.params.server}/>
              </div>
            </div>
          </div>
          <div className="col-xs-12  col-md-6">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h3 className="panel-title">Top countries</h3>
              </div>
              <div className="panel-body aligncenter">
                <CountryChart topcountries={this.state.info.topcountries} server={this.props.match.params.server}/>
              </div>
            </div>
          </div>
        </div>
        {this.state.info.show_server_status ? <ServerStatus server={this.state.server} /> : null}
      </div>
    )
  }
}

export default Home;
