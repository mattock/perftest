#!/usr/bin/awk -f

BEGIN {
	cpu_usr = 0
	cpu_sys = 0
	cpu_total = 0
	cpu_wait = 0
}

# The interesting columns are these:
# $6:    CPU idle (%)
# $10:   memory used (bytes)
# $14:   swap usage (bytes)

# Only match lines starting with a date like this: 26-10
# FIXME: does not work properly with "if" statement
# /^[[:digit:]]+-[[:digit:]]+.*$/

# Set the record separator
{ FS = "," }

{
	# Count all the values together
	cpu_usr = cpu_usr + $4
	cpu_sys = cpu_sys + $5
	cpu_total = cpu_total + (100 - $6)
	cpu_wait = cpu_wait + $7
}


END {
	# Calculate average CPU usage
	cpu_usr = cpu_usr / NR
	cpu_sys = cpu_sys / NR
	cpu_total = cpu_total / NR
	cpu_wait = cpu_wait / NR

	# Print results
	if ( format == "csv" )
        	print test";"subtest";"cpu_usr";"cpu_sys";"cpu_total";"cpu_wait
	else if ( format == "mediawiki" )
        	print "|"test"||"subtest"||"cpu_usr"||"cpu_sys"||"cpu_total"||"cpu_wait"\n|-"
}
