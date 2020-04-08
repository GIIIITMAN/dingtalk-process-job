# -*- coding: UTF-8 -*-
import json
from config import Config
from client import Client
import db
import constants

useAppKey = Config().payload()["USEAPPKEY"]
sdkClient = Client(useAppKey).getInstance()

def run():
	print(useAppKey)
	print(sdkClient)
	processCode = 'PROC-599D7A8F-6FE7-468E-A5AD-1B370DA70611' # 日工
	response = sdkClient.bpms.processinstance_list(processCode, 1544406815)
	# bizData = loadBizData()
	# print(bizData['processCodes'])
	
	# start db operation
	conn = db.Connection().getConnection()
	# db operation here
	# print(query("select * from day_work"))
	mergeDayWork(conn, response)

	conn.close()

def loadBizData():
	file = open(constants.BIZ_DATA_FILENAME)
	content = json.load(file)
	file.close()
	return content

def query(conn, sql):
	cursor = conn.cursor()
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
def isSuccess(data):
	return (data["success"] and data["ding_open_errcode"] == 0)

def mergeDayWork(conn, data):
	voList = data["result"]["list"]["process_instance_top_vo"]
	if isSuccess(data) and voList is not None:
		cursor = conn.cursor()
		insertData = []
		for process in voList:
			componentVoList = process["form_component_values"]["form_component_value_vo"]
			if process["status"] == "COMPLETED" and componentVoList is not None:
				for component in componentVoList:
					// TODO 处理各字段
					insertData.append((process[], process[], component[], component[]))
		
		if len(insertData) != 0:
			sql = "INSERT INTO day_work () VALUES (%s, %s)"
			cursor.executemany(sql, insertData)
		