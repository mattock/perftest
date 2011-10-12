#!/bin/sh
# Convenience wrapper to launch dstat with correct parameters
rm /tmp/dstat.csv
/usr/bin/dstat -t -n -N eth0 -c -m -s --output /tmp/dstat.csv
