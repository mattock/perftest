#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from time import sleep
from fabricconf import fabricconf
import fabric
import testenv
import pprint
import threading

class configurer(threading.Thread):
	"""Thread that's launched to configure an active VM"""

	def __init__(self,id,fc,queue):
		threading.Thread.__init__(self)

		self.id = id
		self.fc = fc
		self.queue = queue

	def run(self):
		while True:

			host = self.queue.get()

			print "configurer-"+ str(self.id) + ": configuring host " + host

			testenv.setup_client(host,self.fc)

			print "configurer-"+ str(self.id) + ": configured host " + host 

			self.queue.task_done()
