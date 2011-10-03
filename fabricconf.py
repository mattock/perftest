#!/usr/bin/python
# -*- coding: utf-8 -*-
#

class fabricconf():

	def __init__(self,username=None,password=None,keyfile=None,tests=[]):
		self.username = username
		self.password = password
		self.keyfile = keyfile
		self.no_agent = True
		self.tests = tests
		self.filesrc = "resources"
		self.vpndst = "/etc/openvpn"

	def __str__(self):
		return self.username
