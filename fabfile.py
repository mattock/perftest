from fabric.api import *
from sys import exit
import datetime
import ConfigParser

# Various global variables
src = "./resources"
vpndst = "/etc/openvpn"

def get_tests():
	"""Get names of the test scripts so that we can upload them"""
	try:
		tconfig = ConfigParser.RawConfigParser()
		tfilename = "config/tests.conf"
		tconfig.readfp(open(tfilename))
	except IOError:
		print "Missing config/tests.conf"
		sys.exit(1)

	# Return a list with all sections
	return tconfig.sections()

def run_except(command):
    """Wrapper for run with exception handling"""
    try:
        run(command)
    except:
	pass

def sudo_except(command):
    """Wrapper for sudo with exception handling"""
    try:
        sudo(command)
    except:
	pass

def put_executables(filesrc,filedst,files):
    """Wrapper to upload files with executable permissions"""
    for file in files:
        put(filesrc+"/"+file,filedst,use_sudo=True)
        set_executable_perms(filedst+"/"+file)

def put_secret_files(filesrc,filedst,files):
    """Wrapper to upload files with strict permissions"""
    for file in files:
        put(filesrc+"/"+file,filedst,use_sudo=True)
        set_strict_perms(filedst+"/"+file)

def set_executable_perms(file):
    """Set executable permissions for a file"""
    sudo_except("chown root:root "+file)
    sudo_except("chmod 755 "+file)

def set_strict_perms(file):
    """Set strict permissions for a file"""
    sudo_except("chown root:root "+file)
    sudo_except("chmod 400 "+file)


def setup_common():
    """Setup things that are common to clients and servers"""
    # We don't want _any_ output from the applications by default. Note that 
    # ntpdate is not needed/usable because on Amazon EC2 domUs are forced to use 
    # the time dom0 provides.
    sudo_except("apt-get -qq -y install iperf openvpn")

    # Upload keys
    keys = ["ta.key","server.crt", "ca.crt"]
    put_secret_files(src,vpndst,keys)


# Task names follow the following format:
#
# setup_<role>
#
# where <role> is given as a parameter to start.py

@task
def setup_server():
    """Setup server-specific things"""
    setup_common()

    # Install performance monitoring tools
    sudo_except("apt-get -qq -y install dstat")

    # Copy server keys
    keys = ["dh1024.pem","server.key"]
    put_secret_files(src,vpndst,keys)

    # Copy server config
    config = ["server.conf"]
    put_secret_files(src,vpndst,config)

    # Launch openvpn and iperf
    sudo_except("/etc/init.d/openvpn restart")

    # Launching iperf using Fabric does not seem to work
    # sudo_except("/usr/bin/iperf -s -D &")

@task
def setup_client():
    """Setup client-specific things"""
    setup_common()

    # Copy OpenVPN client keys and config
    put_secret_files(src,vpndst,["client.crt","client.key","client.conf"])

    # Copy crontab entry
    put_executables(src,"/etc",["crontab"])

    # Copy test scripts
    put_executables(src,"/tmp",get_tests())
