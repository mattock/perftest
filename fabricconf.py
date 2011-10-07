#!/usr/bin/python
# -*- coding: utf-8 -*-
#

class fabricconf():

	def __init__(self,username=None,password=None,keyfile=None,role=None,task=None):
		self.username = username
		self.password = password
		self.keyfile = keyfile
		self.no_agent = True
		self.role = role
		self.task = task

	def __str__(self):
		return self.username
