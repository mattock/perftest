#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# FIXME: passing configuration parameters (e.g. keyfile_name) dynamically to 
# Fabric seems to be pretty difficult: at the moment it does not work at all.
# A Fabric upgrade or subclassing some of it's methods could do the trick.

from fabric.api import *

class testsuite():

    def __init__(self,host,username,password,keyfile,no_agent=True):
        self.host = host
        self.username = username
        self.password = password
        self.key_filename = keyfile
        self.no_agent = no_agent

    def sudo_except(self,command):
        """Wrapper with exception handling for Fabric's sudo method"""
        try:
            sudo(command)
        except:
            pass

    def host_type(self):
        """Testing method to get the host type"""
        run("uname -a")
