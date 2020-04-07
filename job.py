#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import biz
import sys

# python2.7 set default encoding
# reload(sys)
# sys.setdefaultencoding('utf-8')

if __name__ == "__main__":
	print(sys.getdefaultencoding())
	print("dingtalk 审批流任务开始")
	biz.run()
	# TODO 加载处理代码执行任务
	print("dingtalk 审批流任务结束")