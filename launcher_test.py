#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from time import sleep
import threading

# FIXME: reimplement queuing (originally launcher and poller+queuer were in a 
# separate class.
class launcher_test(threading.Thread):
	"""Thread to simulate creation of one or more VMs on Amazon EC2. Only useful for static VM configurations or for Fabric testing."""

	def __init__(self):

		# Run the init function of the superclass
		threading.Thread.__init__(self)

		# List containing IPs of all VMs we want to "create"
		self.ips=["server1.domain.com", "server2.domain.com", "server3.domain.com"]

		# Amount of delay after creating a VM
		self.delay=3

		# A queue containing "activated" VMs
		self.aips = []

	def run(self):
		for ip in self.ips:
			self.aips.append(ip)
			print "launcher_test: IP "+ip+ " now active"
			sleep(self.delay)

		print "launcher_test: done"
