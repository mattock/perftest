#!/usr/bin/awk

# Calculate total amount of data transfered. The relevant lines in iperf output 
# are like this: 
#
# [  3]  0.0-10.0 sec    134 MBytes    112 Mbits/sec


BEGIN { print "Clients;Total transfer (MB);Total bandwidth (Mb/s);Average bandwidth (Mb/s)" }
/MBytes/ { ++clients }
/MBytes/ { mbytes += $5 }
/Mbits/ { mbits += $7 }
END { print clients";"mbytes";"mbits";"mbits/clients }


