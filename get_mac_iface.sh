#!/bin/sh
ip neigh | grep -i "$1" | sed -E 's/^.*dev ([^ ]+).*$/\1/'
