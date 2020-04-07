# -*- coding: UTF-8 -*-

from dingtalk import SecretClient, AppKeyClient
from dingtalk.storage.kvstorage import KvStorage
from config import Config

settings = Config().payload()["DINGTALK"]

class Client(object):
	"""docstring for Client"""
	def __init__(self, isUseAppKey):
		if isUseAppKey:
			# self.client = AppKeyClient(settings["DINGTALK_CORP_ID"],
			# 							settings["DINGTALK_APP_KEY"],
			# 							settings["DINGTALK_APP_SECRET"],
			# 							settings["DINGTALK_TOKEN",
			# 							settings["DINGTALK_AES_KEY"])
			self.client = AppKeyClient(settings["DINGTALK_CORP_ID"],
										settings["DINGTALK_APP_KEY"],
										settings["DINGTALK_APP_SECRET"])
		else:
			self.client = SecretClient(settings["DINGTALK_CORP_ID"],
										settings["DINGTALK_CORP_SECRET"],
										settings["DINGTALK_TOKEN"],
										settings["DINGTALK_AES_KEY"])
		super(Client, self).__init__()

	def getInstance(self):
		return self.client
