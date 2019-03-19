#!/bin/sh

export COVERAGE_FILE=.coverage.unit

py.test -svv --cov-report term-missing --cov=piestats test/

coverage html
