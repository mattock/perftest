#!/usr/bin/python
# -*- coding: utf-8 -*-
#

# Generic classes
import getopt
import sys
import ConfigParser
from os.path import basename
from os.path import splitext

# Custom classes
from launcher_test import launcher_test
from launcher_ec2 import launcher_ec2
from configurer import configurer

def Usage():
	"""Show usage information"""
	print
	print "Usage: start [options]"
	print
	print "Options:"
	print "  -u username  | --username=username      SSH username"
	print "  -p password  | --password=password      SSH password"
	print "  -k keyfile   | --keyfile=keyfile        SSH key filename"
	print "  -s testsuite | --testsuite=testsuite    test suite to run"
	print "  -o provider  | --provider=provider      VM provider"
	print "  -t threads   | --threads=threads        number of configurer (Fabric) threads to allocate"
	print
	print "Available VM providers"
	print_vm_providers()
	print "Available testsuites"
	print_testsuites()
	sys.exit(1)


def print_vm_providers():
	"""Print a list of available VM providers"""
	# FIXME: make this list dynamic
	print "  \"test\" (default, a list of computers in launcher_test.py)"
	print "  \"ec2\" (Amazon EC2 provider)"
	print

def print_testsuites():
	"""Print a list of available testsuites"""
	# FIXME: make this list dynamic
	print "  \"default\""
	print


def error_provider_config_missing(filename):
	"""Print a notification about missing provider configuration and exit"""
	print "Missing provider configuration file ("+filename+")"
	print
	sys.exit(1)

def launch_test():

	config = ConfigParser.RawConfigParser()
	filename = "test.conf"
	try:
		config.readfp(open(filename))
	except:
		error_provider_config_missing(filename)

	# FIXME: Properly implement the test launcher/poller/queuer
	#launchthr = launcher_test()
	#launchthr.start()

def launch_ec2(keyfile):

	config = ConfigParser.RawConfigParser()
	filename = "ec2.conf"
	try:
		config.readfp(open(filename))
	except IOError:
		error_provider_config_missing(filename)

	# Fill in variables and call Amazon EC2 launcher
	try:
		aws_access_key_id = config.get("authentication","aws_access_key_id")
		aws_secret_access_key = config.get("authentication","aws_secret_access_key")
		image_id = config.get("filters","image_id")
		security_group = config.get("filters","security_group")
		instance_type = config.get("instance","instance_type")
	except:
		print "Error in "+filename+", please take a look at "+filename+".sample"

	# Generate key name for Amazon provider from the command-line SSH key option
	key_name = basename(keyfile)
	key_name = splitext(key_name)

	# Launch the provider thread
	launchthr = launcher_ec2(aws_access_key_id,aws_secret_access_key,image_id,instance_type,security_group,key_name[0])
	launchthr.start()

	# Return the provider thread: we need it's queue
	return launchthr

def main():
	"""Main program"""
	# Default variables
	username = None
	password = None
	keyfile = None
	threads = 4
	# FIXME: implement testsuite switching
	testsuite = "default"	
	provider = "test"

	# Parse command-line arguments
	try:
		# Arguments that are followed by a : require a value
                opts, args = getopt.getopt(sys.argv[1:], "hu:p:k:s:o:t:", ["help", "username=", "password=", "keyfile=", "testsuite=", "provider=", "threads="])
        except getopt.GetoptError:
                Usage()
                sys.exit(1)

        for o, a in opts:
                if o in ("-h","--help"):
                        Usage()
                if o in ("-u", "--username"):
                        username = a
                if o in ("-p", "--password"): 
                        password = a
                if o in ("-k", "--keyfile"): 
                        keyfile = a
                if o in ("-s", "--testsuite"):  
                        testsuite = a
                if o in ("-o", "--provider"):  
                        provider = a
                if o in ("-t", "--threads"):
			try:
	                        threads = int(a)
			except ValueError:
				print "WARNING: using default number of threads ("+str(threads)+"): verify your options"

	# Verify sanity of command-line arguments
	if username is None:
		print
		print "ERROR: Missing SSH username"
		Usage()

	if keyfile is None and password is None:
		print
		print "ERROR: Missing SSH keyfile or password!"
		Usage()

	if keyfile is not None and password is not None:
		print
		print "ERROR: Please provide only a keyfile or password, not both"
		Usage()

	if keyfile is None and provider == "ec2":
		print
		print "Error: The ec2 provider requires use of a keyfile"
		Usage()

	if threads < 1:
		print "ERROR: too few threads ("+str(threads)+")"
		Usage()

	# Launch the provider thread
	if provider == "ec2":
		launchthr = launch_ec2(keyfile)
	elif provider == "test":
		print "ERROR: test provider only partially implemented"
		sys.exit(1)
		#launch_test()
	else:
		print "ERROR: invalid provider"
		Usage()

	# Launch configurer threads
	for id in range(1,threads):
		configthr = configurer(id,launchthr.queue,username,password,keyfile)
		# We _don't_ want to make these threads daemonic, or we might 
		# run into nasty issue with half-configured servers
		#configthr.setDaemon(True)
		configthr.start()

if __name__ == "__main__":
	main()
