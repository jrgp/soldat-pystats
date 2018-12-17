import React, { Component} from "react";

class Pager extends Component {
  constructor(props) {
    super(props)
    this.state = {
      pos: 0,
    }

    this.goNext = this.goNext.bind(this)
    this.goBack = this.goBack.bind(this)
  }
  goBack(e) {
    e.preventDefault()
    this.setState((state, props) => {
      state.pos -= props.incr;
      if (state.pos < 0) {
        state.pos = 0;
      }
      this.props.onPagerChange(state.pos)
      return state;
    })
  }
  goNext(e) {
    e.preventDefault()
    if (this.state.pos < (this.props.maxitems + this.props.incr)) {
      this.setState((state, props) => {
        state.pos += props.incr;
        this.props.onPagerChange(state.pos)
        return state;
      })
    }
  }
  render() {
    return (
        <nav>
        <ul className="pager">
        {this.state.pos > 0 ? <li><a href="" onClick={this.goBack}>Previous</a> </li> : <li className="disabled"><a><span aria-hidden="true">Previous</span></a> </li>}

        {this.state.pos < this.props.maxitems - this.props.incr ? <li><a href="" onClick={this.goNext}>Next</a></li> : <li className="disabled"><a><span aria-hidden="true">Next</span></a></li>}
        </ul>
        </nav>
        )

  }
}

export default Pager;
