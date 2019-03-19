#!/bin/sh

export COVERAGE_FILE=.coverage.unit

py.test -sv --cov-report term-missing --cov=piestats test/

coverage html
