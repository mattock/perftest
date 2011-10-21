#!/bin/bash
# Create useful statistics from iperf logs. Uses analyze.awk for the hard 
# lifting.

if [ "$1" == "" ] || ! [ -d "$1" ]; then
	echo "Please give a directory containing log files as the first parameter"
	exit 1
fi

