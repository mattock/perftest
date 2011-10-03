#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from time import sleep
from fabricconf import fabricconf
import fabric
import pprint
import threading
import subprocess

class configurer(threading.Thread):
	"""Thread that's launched to configure an active VM"""

	def __init__(self,id,fc,queue):
		threading.Thread.__init__(self)

		self.id = id
		self.fc = fc
		self.queue = queue
		print "configurer-"+str(self.id)+" reporting in"


	def run(self):
		while True:
			host = self.queue.get()

			print "configurer-"+ str(self.id) + ": configuring host " + host

			# With this style of invocation we run into problems 
			#with parallelism not working properly 
			#testenv.setup_client(host,self.fc)

			# Convert fabricconf object into fab's command-line 
			# arguments. The resulting command-line should look 
			# something like this:
			#
			# fab -a -H 10.118.130.144 -i ~/.ssh/samuli.pem -u ubuntu -w setup_client

			args = ["fab","-a"]
			args.append("-H")
			args.append(host)
			args.append("-i")
			args.append(self.fc.keyfile)
			args.append("-u")
			args.append(self.fc.username)
			args.append("-w")
			args.append("setup_client")

			# Launch a separate process for this instance of Fabric
			fp = subprocess.Popen(args)

			print "configurer-"+ str(self.id) + " finished" 

			self.queue.task_done()
