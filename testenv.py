from fabric.api import *
from fabricconf import fabricconf
import sys
import time
import socket

#### General-purpose methods

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

### Test environment setup methods

def setup_common(fc):
    """Setup things that are common to clients and servers"""
    # We don't want _any_ output from the applications by default. Note that 
    # ntpdate is not needed/usable because on Amazon EC2 domUs are forced to use 
    # the time dom0 provides.
    sudo_except("apt-get -qq -y install iperf openvpn")

    # Upload keys
    keys = ["ta.key","server.crt", "ca.crt"]
    put_secret_files(fc.filesrc,fc.vpndst,keys)


def setup_server(host_string,fc):
    """Setup server-specific things"""
    setup_env(host_string,fc)
    setup_common(fc)

    # Install performance monitoring tools
    sudo_except("apt-get -qq -y install nmon")

    # Copy server keys
    keys = ["dh1024.pem","server.key"]
    put_secret_files(fc.filesrc,fc.vpndst,keys)

    # Copy server config
    config = ["server.conf"]
    put_secret_files(fc.filesrc,fc.vpndst,config)


def setup_client(host_string,fc):
    """Setup client-specific things"""
    setup_env(host_string,fc)
    setup_common(fc)
    # Copy OpenVPN client keys and config
    put_secret_files(fc.filesrc,fc.vpndst,["client.crt","client.key","client.conf"])

    # Copy crontab entry
    put_executables(fc.filesrc,"/etc",["crontab"])

    # Copy test script
    put_executables(fc.filesrc,"/tmp",["tests.sh"])

def setup_env(host_string,fc):
    """Setup env array before calling a Fabric task""" 
    env.host_string=host_string
    env.user=fc.username
    env.password=fc.password
    env.no_agent=fc.no_agent
    env.key_filename=fc.keyfile
