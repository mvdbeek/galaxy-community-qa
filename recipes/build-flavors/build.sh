#!/usr/bin/env bash

# We fail on first error
set -e

# We first need a new IFB instance:

unset HOST
HOST=$(ifbcloud start -n jenkins_kickstart -t c3.medium)  # The credentials come via ENV VARS
