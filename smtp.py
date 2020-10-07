#mpfvwwvvwwgybbie
import smtplib
from email.mime.text import MIMEText
from email.header import Header
def send_email(name,title,content):
	sender="107lsmlsm@whut.edu.cn"
	receivers=["1071100387@qq.com"]
	mail_host="smtphz.qiye.163.com"#设置服务器
	mail_user=""    #邮箱用户名
	mail_pass=""   #邮箱口令  
	message=MIMEText(content,"plain","utf-8")
	message["From"]=Header(name,"utf-8")
	message["To"]=Header("我的邮箱","utf-8")
	subject=title
	message["Subject"]=Header(subject,"utf-8")
	ret_flag=0
	try:
	    smtpObj = smtplib.SMTP_SSL(mail_host,994)
	    smtpObj.login(mail_user,mail_pass)  
	    smtpObj.sendmail(sender, receivers, message.as_string())
	    ret_flag=1
	except smtplib.SMTPException:
	    ret_flag=-1
	return ret_flag