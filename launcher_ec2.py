#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from boto.ec2 import *
from time import sleep
import threading
import Queue
import sys
import base64

class launcher_ec2(threading.Thread):
	"""Threaded class that creates one or more VMs on Amazon"""

	def __init__(self, aws_access_key_id,aws_secret_access_key,image_id,instance_type,instances,security_group,key_name,availability_zone,role):
		""" Initialize this instance"""
		# Run the init function of the superclass
		threading.Thread.__init__(self)

		# Setup variables
		self.aws_access_key_id = aws_access_key_id
		self.aws_secret_access_key = aws_secret_access_key
		self.image_id = image_id
		self.instance_type = instance_type
		self.availability_zone = availability_zone
		self.instances = instances

		# Boto needs an array with security groups
		self.security_groups = []
		self.security_groups.append(security_group)
		self.key_name = key_name

		# A role definition is attached to each instance on EC2 side 
		# (technically as userData attribute). This allows us to avoid 
		# queuing (and thus configuring) wrong VMs, for example an 
		# already running server as a client.
		#
		# TODO: replace with tags when upgrading to Boto 2.0+
		# TODO: replace the current instance filtering scheme with this
		#       approach
		self.role = role

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
			instance_type=self.instance_type,user_data=self.role,placement=self.availability_zone)
			
			# FIXME: test if connection to a to-be-configured server 
			# can be established, instead of using a hack like this
			sleep(30)			

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
						b64userdata=conn.get_instance_attribute(instance.id,"userData")['userData']
						if b64userdata:
							userdata = base64.b64decode(b64userdata)
						else:
							userdata = ""

						# Check if we want to add this instance to the queue. Note that
						# get_instance_attribute does _not_ return one attribute, but a
						# but a dictionary (a bug?)
						if instance.key_name == self.key_name and\
						instance.image_id == self.image_id and\
						instance.instance_type == self.instance_type and\
						instance.state == 'running' and\
						userdata == self.role:
							self.queued_instances.append(ip)
							self.queue.put(ip)
							print "launcher_ec2: queued IP "+ip+"\n" 
						else:
							self.invalid_instances.append(ip)


			# Test if the queue is empty 
			#if self.queued_instances and self.queue.empty():
			#	print "Queue empty, exiting..."
			#	sys.exit(1)
			#else:
			#	print "Entries in queue: "+str(self.queue.qsize())

			# Sleep for a while before next run
			sleep(10)

