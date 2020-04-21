# -*- coding: UTF-8 -*-
import json
from config import Config
from client import Client
import db
import constants
import util

useAppKey = Config().payload()["USEAPPKEY"]
sdkClient = Client(useAppKey).getInstance() # COMMENT OUT IF LOCAL
startTime = 1586044800

def run():
	# print(useAppKey)
	# print(sdkClient)
	# processCode = 'PROC-599D7A8F-6FE7-468E-A5AD-1B370DA70611' # 日工
	# response = sdkClient.bpms.processinstance_list(processCode, 1544406815)
	bizData = loadBizData()
	
	# start db operation
	conn = db.Connection().getConnection()
	# db operation here
	# print(query("select * from day_work"))

	# local test ===========================================
	# file = open("./test-data/single.json")
	# response = json.load(file)
	# print(response)
	# file.close()
	# mergeDayWork(conn, processCode, response)

	# file = open("./test-data/single2.json")
	# response = json.load(file)
	# file.close()
	# mergeContractWork(conn, processCode, response)

	# e059a59a-6d28-4f93-8ff7-0c03c332d2db
	# instId = "e059a59a-6d28-4f93-8ff7-0c03c332d2db"
	# file = open("./test-data/pinst-dw.json")
	# response = json.load(file)
	# file.close()
	# parseSingleDayWork(conn, instId, response)
	# file = open("./test-data/pinst-cw.json")
	# response = json.load(file)
	# file.close()
	# parseSingleContractWork(conn, instId, response)
	# local end =============================================


	#======================================================
	# run on server
	# recheck unloaded process first
	remainProcesses = query(conn, "select id, instance_id, process_type from incomplete_process")
	if remainProcesses is not None:
		for remainProcess in remainProcesses:
			if remainProcess[2] == "DAYWORK":
				response = sdkClient.bpms.processinstance_get(remainProcess[1])
				parseSingleDayWork(conn, remainProcess[1], response)
			elif remainProcess[2] == "CONTRACTWORK":
				response = sdkClient.bpms.processinstance_get(remainProcess[1])
				parseSingleContractWork(conn, remainProcess[1], response)

	for processCode in bizData["processCodes"]["dayWork"]:
		response = sdkClient.bpms.processinstance_list(processCode, startTime)
		mergeDayWork(conn, processCode, response)
	for processCode in bizData["processCodes"]["contractWork"]:
		response = sdkClient.bpms.processinstance_list(processCode, startTime)
		mergeContractWork(conn, processCode, response)
	#========================================================

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
	except Exception as e:
		print(e)
	finally:
		cursor.close()

def delete(conn, sql):
	cursor = conn.cursor()
	try:
		cursor.execute(sql)
		conn.commit()
	except Exception as e:
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
	voList = data["result"]["list"]["process_instance_top_vo"] if "process_instance_top_vo" in data["result"]["list"] else None
	# print(voList)
	if isSuccess(data) and voList is not None:
		# print("valid data")
		cursor = conn.cursor()
		insertData = []
		incompleteTuple = []
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
					insertData.append(row + parseDayWorker(worker))
			else:
				incompleteTuple.append((process["process_instance_id"], "DAYWORK", process["status"], process["process_instance_result"]))
		
		if len(incompleteTuple) != 0:
			addIncompleteProcess(conn, incompleteTuple)

		if len(insertData) != 0:
			# print(insertData)
			sql = "INSERT INTO day_work (instance_id,approval_no,title,approval_status,approval_result,create_time,finish_time,init_id,init_name,init_dept,project_name,building_no,internal_staff,external_staff,attendance_days,daywork_days,daywork_quota,daywork_amount,advance_meal_amount,construction_content) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			cursor.executemany(sql, insertData)
		conn.commit()
		cursor.close()
		nextCurTup = data["result"]["next_cursor"] if "next_cursor" in data["result"] else None,
		if nextCurTup is not None and len(nextCurTup) != 0 and nextCurTup[0] is not None:
			resp = sdkClient.bpms.processinstance_list(processCode, startTime, None, nextCurTup[0])
			mergeDayWork(conn, processCode, resp)


def parseDatetime(datetime):
	return datetime.replace(": ", ":")

def parseDayWorker(worker):
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

def mergeContractWork(conn, processCode, data):
	"""columns sequence
		contractwork_id auto generated
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
		amount
		amount_uppercase
		task_performence
		internal_staff
		external_staff
		construction_content
		building_no
		unit_no
		floor_no
		house_no
		total_floors
		area
		unit_price
		area_amount
		advance_amount
		advance_meal_amount
		remain_amount"""
	voList = data["result"]["list"]["process_instance_top_vo"] if "process_instance_top_vo" in data["result"]["list"] else None
	# print(voList)
	if isSuccess(data) and voList is not None:
		# print("valid data")
		cursor = conn.cursor()
		insertData = []
		incompleteTuple = []
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
				projectName = ""
				amount = 0.0
				amountRMB = ""
				taskPerform = None
				for component in componentVoList:
					componentName = component["name"]
					value = component["value"] if "value" in component else None
					if componentName == "工程项目编号、名称":
						projectName = value
					elif componentName == "金额（元）":
						amount = float(value) if value is not None else 0.0
					elif componentName == "工作面完成情况":
						taskPerform = value
					elif componentName == "各专业班组施工人员情况明细":
						value = component["value"]
						if isinstance(value, str):
							workerList = json.loads(value)
						else:
							workerList = value
				row = row + (projectName, amount, util.amountToRMB(amount), taskPerform)
				# print(workerList)
				for worker in workerList:
					insertData.append(row + parseContractWorker(worker))
			else:
				incompleteTuple.append((process["process_instance_id"], "CONTRACTWORK", process["status"], process["process_instance_result"]))
		
		if len(incompleteTuple) != 0:
			addIncompleteProcess(conn, incompleteTuple)
		
		if len(insertData) != 0:
			# print(insertData)
			sql = "INSERT INTO contract_work (instance_id,approval_no,title,approval_status,approval_result,create_time,finish_time,init_id,init_name,init_dept,project_name,amount,amount_uppercase,task_performence,internal_staff,external_staff,construction_content,building_no,unit_no,floor_no,house_no,total_floors,area,unit_price,area_amount,advance_amount,advance_meal_amount,remain_amount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			cursor.executemany(sql, insertData)
		conn.commit()
		cursor.close()
		nextCurTup = data["result"]["next_cursor"] if "next_cursor" in data["result"] else None,
		if nextCurTup is not None and len(nextCurTup) != 0 and nextCurTup[0] is not None:
			resp = sdkClient.bpms.processinstance_list(processCode, startTime, None, nextCurTup[0])
			mergeContractWork(conn, processCode, resp)

def parseContractWorker(worker):
	buildingNo = None
	internalStuff = None
	externalStuff = None
	constructContent = None
	unitNo = None
	floorNo = None
	houseNo = None
	totalFloors = 0
	area = 0.0
	unitPrice = 0.0
	areaAmt = 0.0
	remainAmt = 0.0
	advAmt = 0.0
	advMealAmt = 0.0
	for item in worker:
		label = item["label"]
		value = item["value"]
		if label == "楼号":
			buildingNo = value
		elif label == "内员姓名":
			internalStuff = value
		elif label == "外员姓名":
			externalStuff = value
		elif label == "施工内容" and value is not None:
			constructContent = ",".join(value)
		elif label == "几单元":
			unit_no = value
		elif label == "几层":
			floorNo = value
		elif label == "户":
			houseNo = value
		elif label == "合计层数":
			totalFloors = int(value)
		elif label == "面积":
			area = float(value)
		elif label == "单价":
			unitPrice = float(value)
		elif label == "包工金额（元）":
			areaAmt = float(value)
		elif label == "剩余应付金额":
			remainAnt = float(value)
		elif label == "预支金额":
			advAmt = float(value)
		elif label == "预支饭票":
			advMealAmt = float(value)
	return (internalStuff, externalStuff, constructContent, buildingNo, unitNo, floorNo, houseNo, totalFloors, area, unitPrice, areaAmt, advAmt, advMealAmt, remainAmt)

def parseSingleDayWork(conn, processInstId, data):
	if data["status"] == "COMPLETED":
		row = (processInstId,
				data["business_id"],
				data["title"],
				data["status"],
				data["result"],
				parseDatetime(data["create_time"]),
				parseDatetime(data["finish_time"]) if "finish_time" in data else None,
				data["originator_userid"],
				data["originator_userid"], # user userid instead of username
				data["originator_dept_id"])
		componentVoList = data["form_component_values"]["form_component_value_vo"]
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
		insertData = []
		for worker in workerList:
			# print(worker)
			insertData.append(row + parseSingleDayWorker(worker))
		# print(insertData)
		if len(insertData) != 0:
			cursor = conn.cursor()
			sql = "INSERT INTO day_work (instance_id,approval_no,title,approval_status,approval_result,create_time,finish_time,init_id,init_name,init_dept,project_name,building_no,internal_staff,external_staff,attendance_days,daywork_days,daywork_quota,daywork_amount,advance_meal_amount,construction_content) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			cursor.executemany(sql, insertData)
			conn.commit()
			cursor.close()
		
		delete(conn, "delete from incomplete_process where instance_id = " + processInstId)

def parseSingleDayWorker(worker):
	return parseDayWorker(worker["rowValue"])

def parseSingleContractWork(conn, processInstId, data):
	if data["status"] == "COMPLETED":
		row = (processInstId,
				data["business_id"],
				data["title"],
				data["status"],
				data["result"],
				parseDatetime(data["create_time"]),
				parseDatetime(data["finish_time"]) if "finish_time" in data else None,
				data["originator_userid"],
				data["originator_userid"], # user userid instead of username
				data["originator_dept_id"])
		workerList = []
		projectName = ""
		amount = 0.0
		amountRMB = ""
		taskPerform = None
		componentVoList = data["form_component_values"]["form_component_value_vo"]
		for component in componentVoList:
			componentName = component["name"]
			value = component["value"] if "value" in component else None
			if componentName == "工程项目编号、名称":
				projectName = value
			elif componentName == "金额（元）":
				amount = float(value) if value is not None else 0.0
			elif componentName == "工作面完成情况":
				taskPerform = value
			elif componentName == "各专业班组施工人员情况明细":
				value = component["value"]
				if isinstance(value, str):
					workerList = json.loads(value)
				else:
					workerList = value
		row = row + (projectName, amount, util.amountToRMB(amount), taskPerform)
		insertData = []
		for worker in workerList:
			# print(worker)
			insertData.append(row + parseSingleContractWorker(worker))
		# print(insertData)
		if len(insertData) != 0:
			cursor = conn.cursor()
			sql = "INSERT INTO contract_work (instance_id,approval_no,title,approval_status,approval_result,create_time,finish_time,init_id,init_name,init_dept,project_name,amount,amount_uppercase,task_performence,internal_staff,external_staff,construction_content,building_no,unit_no,floor_no,house_no,total_floors,area,unit_price,area_amount,advance_amount,advance_meal_amount,remain_amount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			cursor.executemany(sql, insertData)
			conn.commit()
			cursor.close()

		delete(conn, "delete from incomplete_process where instance_id = " + processInstId)

def parseSingleContractWorker(worker):
	return parseContractWorker(worker["rowValue"])


def addIncompleteProcess(conn, processTupleList):
	if len(processTupleList) != 0:
		cursor = conn.cursor()
		sql = "INSERT INTO incomplete_process (instance_id, process_type, checked_date, status, result) value (%s, %s, now(), %s, %s)"
		cursor.executemany(sql, processTupleList)
		conn.commit()
		cursor.close()