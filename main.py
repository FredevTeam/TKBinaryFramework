
# -*- coding: UTF-8 -*-
import os
import json
import glob
import multiprocessing
import worker
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

import subprocess

config = {}
global_log_path = ''


pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-1, maxtasksperchild=3)
result = []


def read_config_file(path):
    if not os.path.exists(path):
        print("config file is not found, please check file")
        return None
    with open(path) as file:
        return json.load(file)
    print('open file faild, please check file type is json')
    return None

# 监测是否有 podspec 文件
def check_has_podspec_file(path):
    pod_list = glob.glob(path + '/*.podspec')
    if len(pod_list) > 0:
        return  pod_list
    return  None


def get_workspace_all_project(path):
    list = []
    for file in os.listdir(path):
        p = os.path.join(path,file)
        if os.path.isdir(p):
            list.append(p)
    return list

def check_xcode():
    status, output = os.popen('xcodebuild -version').readlines()
    if 'error' in result:
        return False
    return True

def callBack(x):
    result.append(x)



def sendEmail(object):
    if "email" in config:
        email = config["email"]
        if ("host" in email) and ("user" in email) and ("port" in email) and ('pass' in email) and ('sender' in email) and('receivers' in email):
            # 创建一个带附件的实例
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            message = MIMEMultipart()

            message['From'] = Header('Framework Binrary Worker', 'utf-8')
            subject = 'Framework Binrary Worker'
            message['Subject'] = Header(subject, 'utf-8')
            # 邮件正文内容
            message.attach(MIMEText('这是{0}运行结果，请尽快查看\n{1}'.format(date, object), 'plain', 'utf-8'))

            logs = glob.glob(global_log_path + '/*{0}*.log'.format(date))
            for l in logs:
                basename = os.path.basename(l)
                # 构造附件1，传送当前目录下的 test.txt 文件
                att = MIMEText(open(l, 'rb').read(), 'base64', 'utf-8')
                att["Content-Type"] = 'application/octet-stream'
                # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
                att["Content-Disposition"] = 'attachment; filename="{0}"'.format(basename)
                message.attach(att)

            smtp = smtplib.SMTP(email['host'],email['port'],timeout=1000)
            smtp.ehlo()
            smtp.starttls()
            smtp.set_debuglevel(1)
            try:
                smtp.login(email['user'], email['pass'])
                smtp.sendmail(email['sender'], email['receivers'], message.as_string())
                print ("邮件发送成功")
                smtp.quit()
                return True
            except smtplib.SMTPException:
                print("Error: 无法发送邮件")
                return  False

    return False


def main(workspace_path,config_file_path, log_path):
    if check_xcode() is False:
        print('please check xcode is not install or need xcode-select default xcode')
        return
    global global_log_path
    global_log_path = log_path

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    if not os.path.exists(workspace_path):
        print('workspace_path:{0} is not exit'.format(workspace_path))
        return

    global config
    config = read_config_file(config_file_path)
    if config is None:
        print("config file is faild , please check")
        return

    workspaces = get_workspace_all_project(workspace_path)

    for dir in workspaces:
        print("===================" + dir)
        pod_file_list = check_has_podspec_file(dir)

        if  pod_file_list is None:
            print("{0} is not has podspec file , please check project".format(pod_file_list))
        else:
            #worker.worker((dir, config, global_log_path))
            #break
            pool.apply_async(worker.worker, args=((dir, config, global_log_path),),callback=callBack)


    pool.close()
    pool.join()
    print(result)
    if len(result) > 0:
        # pass
        sendEmail(result)

if __name__ == '__main__':
    main('/Users/zhuamaodeyu/Documents/LibFramework','./config.json', '/Users/zhuamaodeyu/Documents/LibFramework/log')