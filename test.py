# smtplib module send mail

import smtplib

'''
# 测试邮件发送系统是否正常
TO： 目标邮箱地址 
SUBJECT: 标题 
TEXT： 邮件内容 
gmail_sender： 发送方地址 
gmail_passwd： 发送方密码 
smtp: 邮箱发送服务方地址  
port: 端口号 
'''


TO = 'XXXXXX@163.com'
SUBJECT = 'TEST MAIL'
TEXT = 'Here is a message from python.'

# Gmail Sign In
gmail_sender = 'XXXXXXXXX@gmail.com'
gmail_passwd = 'XXXXXXXX'

smtp = 'smtp.gmail.com'
port = 587

server = smtplib.SMTP(smtp,port,timeout=1000)
server.ehlo()
server.starttls()
server.set_debuglevel(1)
server.login(gmail_sender, gmail_passwd)

BODY = '\r\n'.join(['To: %s' % TO,
                    'From: %s' % gmail_sender,
                    'Subject: %s' % SUBJECT,
                    '', TEXT])

try:
    server.sendmail(gmail_sender, [TO], BODY)
    print('email sent')
    server.quit()
except:
    print('error sending mail')

server.quit()