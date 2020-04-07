# -*- coding: UTF-8 -*-
import json
from config import Config
from client import Client
from db import connection
import constants

useAppKey = Config().payload()["USEAPPKEY"]
# sdkClient = Client(useAppKey).getInstance()

def run():
	print(useAppKey)
	# print sdkClient
	# print(connection)
	processCode = 'PROC-599D7A8F-6FE7-468E-A5AD-1B370DA70611'
	bizData = loadBizData()
	print(bizData['processCodes'])
	# print(sdkClient.bpms.processinstance_list(processCode, 1544406815))
	# print(query("select * from day_work"))

def loadBizData():
	file = open(constants.BIZ_DATA_FILENAME)
	content = json.load(file)
	file.close()
	return content

def query(sql):
	cursor = connection.cursor()
	try:
		cursor.execute(sql)
		row = cursor.fetchone()
		result = []
		while row is not None:
			result.append(row)
			row = cursor.fetchone()
		return result
	except Error as e:
		print(e)
	finally:
		cursor.close()

def finish():
	if connection is not None:
		connection.close()