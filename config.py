# -*- coding: UTF-8 -*-

import json
import constants

class Config(object):
	"""docstring for Config"""
	def __init__(self):
		self.__parse()
		super(Config, self).__init__()

	def __parse(self):
		file = open(constants.CONFIG_FILENAME)
		self.body = json.load(file)
		file.close()

	def payload(self):
		return self.body