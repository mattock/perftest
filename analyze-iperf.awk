#!/usr/bin/awk -f

# Calculate total amount of data transfered. The relevant lines in iperf output 
# are like this: 
#
# [  3]  0.0-10.0 sec    134 MBytes    112 Mbits/sec

/MBytes/ { ++clients }
/MBytes/ { mbytes += $5 }
/Mbits/ { mbits += $7 }
END {

if ( format == "csv" )
	print test";"subtest";"host";"clients";"mbytes";"mbits";"mbits/clients
else if ( format == "mediawiki" )
	print "|"test"||"subtest"||"host"||"clients"||"mbytes"||"mbits"||"mbits/clients"\n|-"
}
