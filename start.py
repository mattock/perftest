#!/usr/bin/python
# -*- coding: utf-8 -*-
#

# Generic classes
import datetime
import getopt
import sys
import ConfigParser
import shutil
from os.path import basename
from os.path import splitext

# Custom classes
from launcher_test import launcher_test
from launcher_ec2 import launcher_ec2
from configurer import configurer
from fabricconf import fabricconf

def Usage():
	"""Show usage information"""
	print
	print "Usage: python start.py [options]"
	print
	print "Options:"
	print "  -u username  | --username=username      SSH username"
	print "  -p password  | --password=password      SSH password"
	print "  -k keyfile   | --keyfile=keyfile        SSH key filename"
	print "  -o provider  | --provider=provider      VM provider"
	print "  -r role      | --role=role              role of the VM; used to select which"
	print "                                          VMs to configure"
	print "  -a task      | --task=task              name of the Fabric task to run on the VMs"
	print "  -i instances | --instances=instances    number of _new_ VM instances to deploy,"
	print "                                          use 0 to only connect to existing ones."
	print "  -t threads   | --threads=threads        number of configurer (Fabric) threads"
	print "                                          to allocate. If 0, skip configuring"
	print "                                          altogether."
	print "  -m remote    | --remote=remote          Remote OpenVPN server (LAN IP)"
        print "  -e peer      | --peer=peer              OpenVPN peer (VPN IP)"
        print
	print "Examples:"
	print
	print "Setup already running instances as test clients using SSH credentials from config/ssh.conf"
	print "and connecting to OpenVPN server at vpn.domain.com."
	print "   python start.py -o ec2 -i 0 -t 4 -r client -a setup_client -m vpn.domain.com"
	print
	print "Create 4 new client instances without configuring anything:"
	print "   python start.py -u user -k ~/.ssh/amazon.pem -o ec2 -i 4 -t 0"
	print
	print "Create 4 new instances and configure all running instances as clients:"
	print "   python start.py -u user -k ~/.ssh/amazon.pem -o ec2 -i 4 -t 4 -r client -a setup_client -m vpn.domain.com"
	print
	print "Download logs from all clients using credentials from config/ssh.conf:"
	print "   python start.py -i 0 -t 4 -r client -a get_client_logs"
	#print
	#print "Available VM providers"
	#print_vm_providers()
	sys.exit(1)


def print_vm_providers():
	"""Print a list of available VM providers"""
	# FIXME: make this list dynamic
	print "  \"local\" (default, a list of computers in launcher_test.py)"
	print "  \"ec2\" (Amazon EC2 provider)"
	print

def error_config_missing(filename):
	"""Print a notification about missing configuration file and exit"""
	print "Missing configuration file ("+filename+")"
	print
	sys.exit(1)

def get_cronjob(mins,command):
	"""Generate a crontab-compatible time definition, or "m h dom mon dow"
	from current time and add <secs> seconds to it. Used to e.g. synchronize OpenVPN 
	client connections to the server. We need to do it here, before Fabric code
	that gets run once per host (using different timestamp)."""

	# For the original idea, look here:
	#
	# http://stackoverflow.com/questions/100210/python-easy-way-to-add-n-seconds-to-a-datetime-time
	ct = datetime.datetime.utcnow()
	lt = ct + datetime.timedelta(seconds=int(mins)*60)
	job = str(lt.minute)+" "+str(lt.hour)+" "+str(lt.day)+" "+str(lt.month)+" * root "+ command+"\n"
	return job

def launch_local():
	"""Launch and queue local VMs"""

	config = ConfigParser.RawConfigParser()
	filename = "config/local.conf"
	try:
		config.readfp(open(filename))
	except:
		error_config_missing(filename)

	# FIXME: Properly implement the test launcher/poller/queuer
	#launchthr = launcher_test()
	#launchthr.start()

def launch_ec2(keyfile,role,instances):
	"""Parse config/ec2.conf and fire up the EC2 launcher thread"""
	config = ConfigParser.RawConfigParser()
	filename = "config/ec2.conf"
	try:
		config.readfp(open(filename))
	except IOError:
		error_config_missing(filename)

	# Parse configuration file
	try:
		aws_access_key_id = config.get("authentication","aws_access_key_id")
		aws_secret_access_key = config.get("authentication","aws_secret_access_key")
		image_id = config.get("filters","image_id")
		security_group = config.get("filters","security_group")
		instance_type = config.get("instance","instance_type")
		availability_zone = config.get("instance","availability_zone")
	except:
		print "Error in "+filename+", please take a look at "+filename+".sample"
		sys.exit(1)

	# Generate key name for Amazon provider from the command-line SSH key option
	key_name = basename(keyfile)
	key_name = splitext(key_name)

	# Launch the provider thread
	launchthr = launcher_ec2(aws_access_key_id,aws_secret_access_key,image_id,instance_type,instances,security_group,key_name[0],availability_zone,role)
	launchthr.start()

	# Return the provider thread: configurer threads need access to it's queue
	return launchthr

def create_testsuite(remote,peer):
	"""Generate all dynamic files needed for controlling the tests on the client-side. Static files are placed in ./resources/"""

	try:
		tconfig = ConfigParser.RawConfigParser()
		tfilename = "config/tests.conf"
		tconfig.readfp(open(tfilename))
	except IOError:
		error_config_missing(tfilename)
		sys.exit(1)

	try:
		cconfig = ConfigParser.RawConfigParser()
		cfilename = "config/cron.conf"
		cconfig.readfp(open(cfilename))
	except IOError:
		error_config_missing(cfilename)
		sys.exit(1)

	# Generate crontab from config/tests.conf and config/cron.conf, mostly 
	# for timing the tests accurately.
	sections = tconfig.sections()

	try:
		crontab = open("./resources/crontab","w")
		crontab.write("SHELL="+cconfig.get("cron","shell")+"\n")
		crontab.write("PATH="+cconfig.get("cron","path")+"\n")

		for section in sections:
			test = {}
			test['testscript'] = section
			test['remote'] = remote
			test['peer'] = peer
			test['time'] = tconfig.get(section,"time")
			crontab.write(get_cronjob(test['time'],"/tmp/"+test['testscript']+" "+test['remote']+" "+test['peer']))
			#tests.append(test)
		crontab.close()

	except ConfigParser.Error:
		print "Error in "+filename+", please take a look at "+filename+".sample"
		sys.exit(1)
		
	except IOError:
		error_config_missing(filename)
		sys.exit(1)

	#return tests

def main():
	"""Main program"""
	# Fabric-specific variables are wrapped into an object for convenience
	fc = fabricconf()

	# Default variables
	threads = 1
	provider = "ec2"
	role = "client"
	instances = 0
	fc.task = "setup_client"
	remote = None
	peer = None

	# Load configuration settings from ssh.conf. Anything given on the 
	# command-line will override these.
	try:
		sshconfig = ConfigParser.RawConfigParser()
		sshfilename = "config/ssh.conf"
		sshconfig.readfp(open(sshfilename))
	except IOError:
		pass

	authdetails = {}
	for i in ["username","keyfile","password"]:
		try:
			authdetails[i] = sshconfig.get("ssh",i)
		except:
			authdetails[i] = None

	fc.username = authdetails["username"]
	fc.keyfile = authdetails["keyfile"]
	fc.password = authdetails["password"]

	# Parse command-line arguments
	try:
		# Arguments that are followed by a : require a value
                opts, args = getopt.getopt(sys.argv[1:], "hu:p:k:o:r:a:i:t:m:e:",\
		["help", "username=", "password=", "keyfile=", "provider=",\
		"role=", "task=", "instances=", "threads=", "remote=", "peer="])
        except getopt.GetoptError:
                Usage()
                sys.exit(1)

        for o, a in opts:
                if o in ("-h","--help"):
                        Usage()
                if o in ("-u", "--username"):
			fc.username = a
                if o in ("-p", "--password"): 
                        fc.password = a
                if o in ("-k", "--keyfile"):
                        fc.keyfile = a
                if o in ("-o", "--provider"):
                        provider = a
		if o in ("-t", "--threads"):
			threads = int(a)
                if o in ("-r", "--role"):
                        role = a
                if o in ("-a", "--task"):
                        fc.task = a
                if o in ("-i", "--instances"):
                        instances = int(a)
                if o in ("-m", "--remote"):
			remote = a
                if o in ("-e", "--peer"):
			peer = a

	if remote is not None and peer is not None:
		create_testsuite(remote,peer)

	# FIXME: implement dynamic peer definitions in tests
	#if peer is None:
	#	print "Option \"peer\" missing!"
	#	Usage()


	# Launch the provider thread
	if provider == "ec2":
		launchthr = launch_ec2(fc.keyfile,role,instances)
	elif provider == "test":
		print "ERROR: test provider only partially implemented"
		sys.exit(1)
	else:
		print "Skipping provisioning as requested."

	# Launch configurer threads
	if threads == 0:
		print "No configurer threads, skipping configuration part."
	else:
		for id in range(0,threads):
			configthr = configurer(id,fc,launchthr.queue)
			configthr.setDaemon(False)
			configthr.start()
	sys.exit(0)

if __name__ == "__main__":
	main()
