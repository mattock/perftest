#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from boto.ec2 import *
from time import sleep
import socket
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
			
			# FIXME: try to make the connection test (below) to work; it is not yet bulletproof
			sleep(60)

		# Start polling for activated instances.
		#
		# FIXME: Currently this polling goes on forever, but could be 
		# stopped when
		#
		# a) certain amount of time has passed since a new VM was activated
		# b) when the number of active VMs equals number of launched VMs.
		while True:
			print "Polling for activated instances...\n"

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
							#print "Debug: b64userdata = " +b64userdata
							userdata = base64.b64decode(b64userdata)
						else:
							userdata = ""
							b64userdata = ""

						#print "Debug: userdata  =   "+ userdata
						#print "Debug: self.role =   "+ self.role
						#print "---"

						# Check if we want to add this instance to the queue. Note that
						# get_instance_attribute does _not_ return one attribute, but a
						# but a dictionary (a bug?)
						if instance.key_name == self.key_name and\
						instance.instance_type == self.instance_type and\
						instance.state == 'running' and\
						userdata == self.role:

							try:
								# Check if SSH is responding. If we don't do this,
								# we get occasional "Connection refused" failures.
								# NOTE: this could potentially lead into long deployment
								# delays if a few servers are unresponsive.
								#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
								#s.connect((ip, 22))
								#s.close()

								# If it was, add the instance to the queue
								self.queued_instances.append(ip)
								self.queue.put(ip)
								print "launcher_ec2: queued IP "+ip+"\n" 
							except:
								pass														

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

