# 审批流任务

## 环境依赖
- Python >2.7
- 加密库兼容 cryptography 和 PyCrypto，优先使用 cryptography
  >pip install cryptography
- dingtalk-sdk，推荐使用 pip 进行安装
  >pip install dingtalk-sdk[cryptography]
- 升级sdk到最新版本
  >pip install -U dingtalk-sdk
- mysql连接库
  >pip install mysql-connector

## 环境变量
>export PYTHONIOENCODING=utf8

## 调用API所需要的KEY
以下KEY需要写入配置文件
>TOKEN         钉钉企业加密解密token
>AES_KEY       钉钉企业加密解密aes_key
>CORP_SECRET   钉钉企业Secret
>CORP_ID       钉钉企业号
>APP_KEY       钉钉企业AppKey
>APP_SECRET    钉钉企业AppSecret

## 数据库
MySQL

## 其他
系统需支持中文