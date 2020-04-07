# -*- coding: UTF-8 -*-
import mysql.connector
from config import Config

dbConfig = Config().payload().get("DB")

try:
	connection = mysql.connector.connect(
		host = dbConfig.get("HOST"),
		user = dbConfig.get("USERNAME"),
		password = dbConfig.get("PASSWORD"),
		port = dbConfig.get("PORT"),
		database = dbConfig.get("SCHEMA"),
		charset = "utf8")
except mysql.connnector.Error as e:
	print("connect failed: {}".format(e))

