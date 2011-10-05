#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is a simple module to terminate all Amazon EC2 instances matching the 
# filters in config/ec2.conf.

import datetime
import getopt
import sys
import ConfigParser
import base64
from boto.ec2 import *

def Usage():
	"""Show usage information"""
	print
	print "Usage: python stop.py [options]"
	print
	print "Options:"
	print
        print "  -r role      | --role=role        role of the VMs to terminate"
	print

def main():

	# Parse command-line arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hr:", ["help", "role="])
	except getopt.GetoptError:
		Usage()
		sys.exit(1)

	for o, a in opts:
                if o in ("-h","--help"):
                        Usage()
                if o in ("-r", "--role"):
			role = a

	# Bail out if a valid role definition is not given
	if not role:
		print "Please define a role!"
		Usage()

	# Parse config/ec2.conf
	config = ConfigParser.RawConfigParser()
	filename = "config/ec2.conf"
	try:
		config.readfp(open(filename))
	except IOError:
		error_config_missing(filename)

	try:
		aws_access_key_id = config.get("authentication","aws_access_key_id")
		aws_secret_access_key = config.get("authentication","aws_secret_access_key")
	except:
		print "Error in "+filename+", please take a look at "+filename+".sample"
		sys.exit(1)


	# Establish EC2 connection
	conn = EC2Connection(aws_access_key_id,aws_secret_access_key)

	# Add matching instances to the "to be terminated" array
	to_be_terminated=[]

	reservations = conn.get_all_instances()
	for reservation in reservations:
		for instance in reservation.instances:
			b64userdata=conn.get_instance_attribute(instance.id,"userData")['userData']
			if b64userdata:
				userdata = base64.b64decode(b64userdata)
			else:
				userdata = ""

			if userdata == role:
				print instance.id+" is being terminated"
				to_be_terminated.append(instance.id)

	# Terminate instances
	conn.terminate_instances(to_be_terminated)


if __name__ == "__main__":
	main()

