#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from time import sleep
from fabtasks import *
from testsuite import testsuite
import pprint
import threading

class configurer(threading.Thread):
	"""Thread that's launched to configure an active VM"""

	def __init__(self,id,queue,username=None,password=None,keyfile=None):
		threading.Thread.__init__(self)

		self.id = id
		self.username = username
		self.password = password
		self.keyfile = keyfile
		self.no_agent = True
		self.queue = queue

	def run(self):
		while True:
			host = self.queue.get()

			print "configurer-"+ str(self.id) + ": configuring host " + host

			# FIXME: this is where Fabric is called. Unfortunately, 
			# Fabric is somewhat inflexible so atm integration isnot 
			# working.

			# Create a new testsuite instance
			#tests = testsuite(host,self.username,self.password,self.keyfile,self.no_agent)

			# Launch a test
			#tests.host_type()

			print "configurer-"+ str(self.id) + ": configured host " + host 

			self.queue.task_done()
