# -*- coding: UTF-8 -*-
import mysql.connector
from config import Config

dbConfig = Config().payload().get("DB")

class Connection(object):
	def __init__(self):
		try:
			self.connection = mysql.connector.connect(
				host = dbConfig.get("HOST"),
				user = dbConfig.get("USERNAME"),
				password = dbConfig.get("PASSWORD"),
				port = dbConfig.get("PORT"),
				database = dbConfig.get("SCHEMA"),
				charset = "utf8")
		except mysql.connnector.Error as e:
			print("connect failed: {}".format(e))
			self.connection = None

	def close(self):
		if self.connection is not None:
			self.connection.close()

	def getConnection(self):
		return self.connection