#!/usr/bin/awk -f

# Calculate total amount of data transfered. The relevant lines in iperf output 
# are like this: 
#
# [  3]  0.0-10.0 sec    134 MBytes    112 Mbits/sec

/MBytes/ { ++clients }
/MBytes/ { transfer += $5 }
/MBytes/ { bandwidth += $7 }
END {

if ( format == "csv" )
	print test";"subtest";"host";"clients";"transfer";"bandwidth";"bandwidth/clients
else if ( format == "mediawiki" )
	print "|"test"||"subtest"||"host"||"clients"||"transfer"||"bandwidth"||"bandwidth/clients"\n|-"
else if ( format == "trac" )
	print "||"test"||"subtest"||"host"||"clients"||"transfer"||"bandwidth"||"bandwidth/clients"||"

}
