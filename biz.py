# -*- coding: UTF-8 -*-
import json
from config import Config
from client import Client
import db
import constants

useAppKey = Config().payload()["USEAPPKEY"]
sdkClient = Client(useAppKey).getInstance()
startTime = 1586044800

def run():
	print(useAppKey)
	# print(sdkClient)
	# processCode = 'PROC-599D7A8F-6FE7-468E-A5AD-1B370DA70611' # 日工
	# response = sdkClient.bpms.processinstance_list(processCode, 1544406815)
	bizData = loadBizData()
	
	# start db operation
	conn = db.Connection().getConnection()
	# db operation here
	# print(query("select * from day_work"))
	# file = open("./test-data/single.json")
	# response = json.load(file)
	# print(response)
	# file.close()
	for processCode in bizData["processCodes"]["dayWork"]:
		response = sdkClient.bpms.processinstance_list(processCode, startTime)
		mergeDayWork(conn, processCode, response)

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

def mergeDayWork(conn, processCode, data):
	"""columns sequence
		daywork_id auto genrate
		instance_id
		approval_no
		title
		approval_status
		approval_result
		create_time
		finish_time
		init_id
		init_name
		init_dept
		project_name
		building_no
		internal_staff
		external_staff
		attendance_days
		daywork_days
		daywork_quota
		daywork_amount
		advance_meal_amount
		construction_content"""
	voList = data["result"]["list"]["process_instance_top_vo"]
	# print(voList)
	if isSuccess(data) and voList is not None:
		print("valid data")
		cursor = conn.cursor()
		insertData = []
		for process in voList:
			componentVoList = process["form_component_values"]["form_component_value_vo"]
			if process["status"] == "COMPLETED" and componentVoList is not None:
				row = (process["process_instance_id"],
								process["business_id"],
								process["title"],
								process["status"],
								process["process_instance_result"],
								# None,
								# None,
								parseDatetime(process["create_time"]),
								parseDatetime(process["finish_time"]) if "finish_time" in process else None,
								process["originator_userid"],
								process["originator_userid"], # user userid instead of username
								# process["originator_username"] if "originator_username" in process else None,
								process["originator_dept_id"])
				workerList = []
				for component in componentVoList:
					componentName = component["name"]
					if componentName == "工程项目编号、名称":
						row = row + (component["value"],)
					elif componentName == "各专业班组施工人员情况明细":
						value = component["value"]
						if isinstance(value, str):
							workerList = json.loads(value)
						else:
							workerList = value
				# print(workerList)
				for worker in workerList:
					insertData.append(row + parseWorker(worker))
		
		if len(insertData) != 0:
			print(insertData)
			sql = "INSERT INTO day_work (instance_id,approval_no,title,approval_status,approval_result,create_time,finish_time,init_id,init_name,init_dept,project_name,building_no,internal_staff,external_staff,attendance_days,daywork_days,daywork_quota,daywork_amount,advance_meal_amount,construction_content) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			cursor.executemany(sql, insertData)
		conn.commit()
		cursor.close()
		nextCur = data["next_cursor"] if "next_cursor" in data else None,
		if nextCur is not None:
			resp = sdkClient.bpms.processinstance_list(processCode, startTime, None, nextCur)
			mergeDayWork(conn, processCode, resp)


def parseDatetime(datetime):
	return datetime.replace(": ", ":")

def parseWorker(worker):
	buildingNo = None
	internalStuff = None
	externalStuff = None
	attendDays = 0.0
	dayworkDays = 0.0
	dayworkQuota = 0.0
	dayworkAmt = 0.0
	advMealAmt = 0.0
	constructContent = None
	for item in worker:
		label = item["label"]
		value = item["value"]
		if label == "楼号":
			buildingNo = value
		elif label == "内员姓名":
			internalStuff = value
		elif label == "外员姓名":
			externalStuff = value
		elif label == "出勤天数":
			attendDays = float(value)
		elif label == "日工天数":
			dayworkDays = float(value)
		elif label == "日工定额":
			dayworkQuota = float(value)
		elif label == "日工金额":
			dayworkAmt = float(value)
		elif label == "支饭票金额":
			advMealAmt = float(value)
		elif label == "施工内容" and value is not None:
			constructContent = ",".join(value)
	return (buildingNo, internalStuff, externalStuff, attendDays, dayworkDays, dayworkQuota, dayworkAmt, advMealAmt, constructContent)