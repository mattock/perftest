#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from boto.ec2 import *
from time import sleep
import threading
import Queue

class launcher_ec2(threading.Thread):
	"""Threaded class that creates one or more VMs on Amazon"""

	def __init__(self, aws_access_key_id,aws_secret_access_key,image_id,instance_type,instances,security_group,key_name):
		""" Initialize this instance"""
		# Run the init function of the superclass
		threading.Thread.__init__(self)

		# Setup variables
		self.aws_access_key_id = aws_access_key_id
		self.aws_secret_access_key = aws_secret_access_key
		self.image_id = image_id
		self.instance_type = instance_type
		self.instances = instances

		# Boto needs an array with security groups
		self.security_groups = []
		self.security_groups.append(security_group)
		self.key_name = key_name

                # We need to separately track instances which have been put to 
                # the queue to avoid rerunning Fabric commands on same servers;
                # Queue class itself has no notion of history, and Boto always
                # returns the full list of active VMs. Look here for additional
                # details:
                #
                # http://stackoverflow.com/questions/1581895/how-check-if-a-task-is-already-in-python-queue
                self.queued_instances = []

		# To save time, we put irrelevant instances to an "invalid" 
		# list. Irrelevant in this context means VMs we _don't_ want to 
		# touch.
		self.invalid_instances = []

		# We need a queue where configurer threads pull their jobs from
		self.queue = Queue.Queue()

	def run(self):
		"""Create VM instances on EC2 and queue them when they're running"""

		# Establish EC2 connection
		conn = EC2Connection(self.aws_access_key_id,self.aws_secret_access_key)

		# Create new VM instances (if requested)
		#
		if self.instances > 0:
			reservation = conn.run_instances(image_id=self.image_id,min_count=1,max_count=self.instances,\
			key_name=self.key_name,security_groups=self.security_groups,\
			instance_type=self.instance_type,placement=None)			

		# Start polling for activated instances.
		#
		# FIXME: Currently this polling goes on forever, but could be 
		# stopped when
		#
		# a) certain amount of time has passed since a new VM was activated
		# b) when the number of active VMs equals number of launched VMs.
		while True:

			# Check if there are any new active and valid instances
		        reservations = conn.get_all_instances()
			for reservation in reservations:
				for instance in reservation.instances:
					ip = instance.public_dns_name
					# Check if this instance is present in the "invalid" or
					# "already queued" lists
					if ip in self.invalid_instances or ip in self.queued_instances:
						pass
					else:
						# Check if we want to add this instance to the queue 
						if instance.key_name == self.key_name and\
						instance.image_id == self.image_id and\
						instance.instance_type == self.instance_type and\
						instance.state == 'running':
							self.queued_instances.append(ip)
							self.queue.put(ip)
							print "launcher_ec2: queued IP "+ip 
						else:
							self.invalid_instances.append(ip)

			# Debugging information
			#print "Queued: "+str(self.queued_instances)
			#print "Invalid: "+str(self.invalid_instances)

			# Sleep for a while before next run
			sleep(10)
