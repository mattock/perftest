#!/bin/bash
# Create useful statistics from iperf logs. Uses analyze.awk for the hard 
# lifting.

if [ "$1" == "" ] || ! [ -d "$1" ]; then
	echo "Please give a directory containing log files as the first parameter"
	exit 1
fi

if [ "$2" == "" ]; then
	echo "Please give the output format (csv, mediawiki, trac) as the second parameter"
fi

LOGDIR=$1
TEST=`basename $LOGDIR`
AWK_IPERF="$LOGDIR/../../analyze-iperf.awk"
AWK_DSTAT="$LOGDIR/../../analyze-dstat.awk"

# Second parameter determines the output format
ANALYSIS_IPERF="$LOGDIR/analysis-iperf.$2
ANALYSIS_DSTAT="$LOGDIR/analysis-dstat.$2

# Remove old analysis files
rm -f $LOGDIR/analysis-*

# Analyze (client) iperf logs
PATTERNS="10s 30s 60s"

# Print headers
if [ "$2" == "csv" ]; then

cat > $LOGDIR/analysis-iperf.$2 << EOF
Test;Subtest;Host;Clients;Total transfer (MB);Total bandwidth (Mb/s);Average bandwidth (Mb/s)
EOF

elif [ "$2" == "mediawiki" ]; then

cat > $LOGDIR/analysis-iperf.$2 <<EOF
{| border="1" style="text-align:center;"
|'''Test'''||'''Subtest'''||'''Host'''||'''Clients'''||'''Total transfer (MB)'''||'''Total bandwidth (Mb/s)'''||'''Average bandwidth (Mb/s)'''
|-
EOF

fi

for PATTERN in $PATTERNS; do
	# Aeverage figures
	$AWK_IPERF format=$2 test=$TEST subtest=$PATTERN host=average $LOGDIR/iperf-$PATTERN*|tee -a $LOGDIR/analysis-iperf.$2
	x=1
	# Per-client figures
	#for FILE in $(ls $LOGDIR/iperf-$PATTERN*); do
	#	$AWK_IPERF format=$2 test=$TEST subtest=$PATTERN host=client$x $FILE|tee -a $LOGDIR/analysis-iperf.$2
	#	x=$(( x + 1 ))
	#done
done

# Print footers
if [ "$2" == "mediawiki" ]; then
	echo "|}" >> $LOGDIR/analysis-iperf.$2
fi


# Analyze the dstat logs from the server.
#
# NOTE TO SELF: trying to detect test boundaries in automated fashion is not 
# trivial, whether using awk or bash.

# FIXME: This echo would be better to have in the awk script itself

if [ "$2" == "csv" ]; then

echo "Test;Subtest;CPU usr (%);CPU sys (%);CPU total (%);CPU wait (%)" >> $LOGDIR/analysis-dstat.$2

elif [ "$2" == "mediawiki" ]; then

cat > $LOGDIR/analysis-dstat.$2 <<EOF
{| border="1" style="text-align:center;"
|'''Test'''||'''Subtest'''||'''CPU usr (%)'''||'''CPU sys (%)'''||'''CPU total (%)'''||'''CPU wait (%)'''
|-
EOF

fi


# Parse the logs
for PATTERN in $PATTERNS; do
	$AWK_DSTAT format=$2 test=$TEST subtest=$PATTERN $LOGDIR/dstat-$PATTERN.csv|tee -a $LOGDIR/analysis-dstat.$2
done

# Print footers
if [ "$2" == "mediawiki" ]; then
	echo "|}" >> $LOGDIR/analysis-dstat.$2
fi
