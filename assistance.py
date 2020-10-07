import requests as Re
import execjs as jsexe
import re
import time
from smtp import send_email
user=""
pd=""#你的账号密码
rsa_key=""
lt_str=""
execution=""
vatify_code=""
s=Re.Session()
login_flag=0
class_list_info=[]
records_file="/home/lsm/class_assistance/inform_records.dat"
#python参数传递 永远是传递指针而不是新分配空间 再拷贝，因此对函数内部的参数进行修改，会修改传入的变量
#python变量作用域 全局变量在函数中使用时，只能读，不能写（改） 需要写，就要在函数里声明 global 全局变量名

#该函数返回上个月1号这个时间的时间戳
def syntax_class_column(classid):
	f=open(records_file,"r")
	lines=f.readlines()
	f.close()
	ret=""
	for x in lines:
		result=re.match("(column )([\d]+)( )([\S]*)",x)
		if(result):
			class_id=re.match("(column )([\d]+)( )([\S]*)",x)[2]
			column_str=re.match("(column )([\d]+)( )([\S]*)",x)[4]
			if(class_id==classid):
				ret=column_str
				break
	assert(len(ret)>1)
	return ret
def last_month_timestamp():
	
	time_str=""
	now_tuple=time.localtime(time.time())
	if(now_tuple[1]==1):
		time_str="{0}-{1}-{2} {3}:{4}:{5}".format(now_tuple[0]-1,12,1,now_tuple[3],now_tuple[4],now_tuple[5])
	else:
		time_str="{0}-{1}-{2} {3}:{4}:{5}".format(now_tuple[0],now_tuple[1]-1,1,now_tuple[3],now_tuple[4],now_tuple[5])
	
	return int(time.mktime(time.strptime(time_str,"%Y-%m-%d %H:%M:%S")))
#以下函数查看本地课程通知最后读取时间的时间戳 int 如果没有记录就返回上个月1号的时间戳（int），
def syntax_class_records(classid):
	f=open(records_file,"r")
	lines=f.readlines()
	f.close()
	last_time_rec=last_month_timestamp()
	for x in lines:
		result=re.match("([\d]+)( )(.*)",x)
		if(result):
			class_id=re.match("([\d]+)( )(.*)",x)[1]
			last_time_str=re.match("([\d]*)( )([\d]*)",x)[3]
			if(class_id==classid and int(last_time_str)>last_time_rec):
				last_time_rec=int(last_time_str)
				break
	return last_time_rec
def login_index(session):
	global login_flag
	global class_list_info
	global rsa_key
	global lt_str
	global execution
	global vatify_code
	res=session.get("http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fjxpt.whut.edu.cn%3A81%2Fmeol%2Fhomepage%2Fcommon%2Fsso_login.jsp")
	#<input type="hidden" id="lt" name="lt" value="LT-748312-6ualcdMgkORamuLjzbiNZKYe9AZmi6-tpass" />
	lt_str=re.search("(<.*?id.*?\"lt\".*?value.*?\")([^\"\n]*?)(\")",res.text)[2]#第二段即是lt
	#<input type="hidden" name="execution" value="e3s2" />
	execution=re.search("(<.*?name.*?execution.*?value.*?\")(.*?)(\")",res.text)[2]
	f=open("/home/lsm/class_assistance/des.js","r")
	jsfile=f.read()
	f.close()
	ctx=jsexe.compile(jsfile)
	rsa_key=ctx.call("strEnc",user+pd+lt_str,"1","2","3")
	data_to_send={"rememberName":"on",\
		"rsa":rsa_key,\
		"ul":str(len(user)),\
		"pl":str(len(pd)),\
		"lt":lt_str,\
		"execution":execution,\
		"_eventId":"submit"}
	if(res.text.find("id=\"vali\"")>0):
		print("要输入验证码！")
		img_src="http://zhlgd.whut.edu.cn/tpass/code"#暂时是不变的 懒得解析了
		res=session.get(img_src)
		f=open("/home/lsm/vatify.jpeg","wb+")
		f.write(res.content)
		f.close()
		vatify_code=str(input("请查看并输入验证码！保存在/home/lsm/vatify.jpeg"))
		data_to_send["code"]=vatify_code
	res=session.post("http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fzhlgd.whut.edu.cn%2Ftp_up%2F",data=data_to_send)
	if(len(res.history)>0 and res.text.find("在线人数")>0):
		print("login success")
		login_flag=1
	else:
		print("login fail")
#此函数传入三个参数 1会话session,2课程id,3学习资源所在的栏目名字
def view_class_index_page(session,classid,column_name):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/layout/newpage/index.jsp",\
		params={"courseId":str(classid)})
	#menuUrl('0','73837','课程学习','1',$(this))
	columnid=re.search("(menuUrl.*?,')([\d]*)(','"+column_name+")",res.text)[2]
	res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/course_column_preview_transfer.jsp",\
		params={"tagbug":"client","columnId":str(columnid)})
def study_class_over_time(session,classid):
	res=session.post("http://jxpt.whut.edu.cn:81/meol/lesson/onlinetime_listener.jsp",\
		data={"lessId":str(classid)})
	if(res.text.find("success\",\"status\":0")>0):
		print("已经学习一分钟了！")
def syntax_study_info(study_html_text):
	ret=[]
	study_time=re.search("(本课程网络学习总时长[\S\s]*?needstar\">[\s]*)([\d]*)",study_html_text)[2]
	ret.append(study_time)
	return ret
def get_study_info(session,classid,uid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/common/newscoremanagement/stu_course_detail.jsp",\
		params={"lid":str(classid),"uid":str(uid)})
	return syntax_study_info(res.text)
def class_syntax(class_li_text):
	ret=[]
	#<span class='realname'>张进</span>
	#courseId=
	class_name=re.search("(title[\S\s]*?>[\S\s]*?>[\s]*)([\S]*)",class_li_text)[2]
	teacher_name=re.search("(realname.*?>)([\S]*)(</span)",class_li_text)[2]
	class_id=re.search("(courseId=)([\d]*)",class_li_text)[2]
	ret.append(class_name)
	ret.append(teacher_name)
	ret.append(class_id)
	return ret
def get_all_class_info(session):
	#登陆之后的事情
	global login_flag
	global class_list_info
	if(login_flag==1):
		#获取课程列表
		res=session.get("http://jxpt.whut.edu.cn:81/meol/welcomepage/student/course_list_v8.jsp")
		pattern=re.compile("<li>[\s\S]*?</li>")
		class_list_text=pattern.findall(res.text)
		for x in class_list_text:
			class_list_info.append(class_syntax(x))
		assert(len(class_list_info)>0)
		#获取课程学习时长：
		index=0
		for x in class_list_info:
			x.append(get_study_info(s,x[2],"159857"))
			print("编号",index,end=":")
			index=index+1
			print(x)

def get_class_inform(session,classid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/common/inform/index_stu.jsp",\
		params={"tagbug":"client","s_order":"0","lid":str(classid),"strStyle":"new06"})
	ctx=re.compile("(<tr>[\s\S]*?<td>[\s\S]*?</td>[\s\S]*?</tr>)")
	class_inform_text=ctx.findall(res.text)
	class_unread_inform_list=[]
	index=0
	for x in class_inform_text:
		try:
			single_inform=[]
			informid=re.search("(jsp\?nid=)([\d]*)",x)[2]
			inform_title=re.search("(title=\")([\S\s]*?)(\"\n *onClick)",x)[2]
			#class="align_c">罗先平
			inform_time=re.search("(<td[\s\S]*?\"align_c\">)(.*?)(\n[\s\S]*?\"align_c\">)(.*?)(\n)",x)[2]
			inform_time=int(time.mktime(time.strptime(inform_time,"%Y-%m-%d %H:%M:%S")))
			inform_sender=re.search("(<td[\s\S]*?\"align_c\">)(.*?)(\n[\s\S]*?\"align_c\">)(.*?)(\n)",x)[4]
			if(inform_time>=syntax_class_records(classid)):
				single_inform.append(informid)
				single_inform.append(inform_title)
				single_inform.append(inform_sender)
				single_inform.append(inform_time)
				class_unread_inform_list.append(single_inform)
				index=index+1
		except:
			continue
	return class_unread_inform_list



class_list_info=[]
login_index(s)
get_all_class_info(s)
index=int(input("请选择一个课程自动学习（输入对应的数字编号）:"))
column_name=syntax_class_column(class_list_info[index][2])



class_list_info[index].append(get_class_inform(s,class_list_info[index][2]))
while(1):
	time.sleep(10)
	try:
		class_list_info[index][4]=get_class_inform(s,class_list_info[index][2])
		for x in class_list_info[index][4]:
				flag=send_email(class_list_info[index][0],"{}-{}-{}".format(x[1],x[2],time.strftime("%Y-%m-%d %H:%M:%S",\
					time.localtime(x[3]))),"暂未查看")
				if(flag==1):
					print("通知未读，邮件提醒")
					f=open(records_file,"a+")
					f.writelines(["{} {}".format(class_list_info[index][2],x[3])])
		now_tuple=time.localtime(time.time())
		if(int(now_tuple[3])==12 and int(now_tuple[4])>8):
			#刷新登陆状态
			print("到时间了开始学习")
			rsa_key=""
			lt_str=""
			execution=""
			vatify_code=""
			s=Re.Session()
			login_flag=0
			class_list_info=[]
			login_index(s)
			get_all_class_info(s)
			class_list_info[index].append(get_class_inform(s,class_list_info[index][2]))
			view_class_index_page(s,class_list_info[index][2],column_name)
			cnt=0
			while(1):
				class_list_info[index][4]=get_class_inform(s,class_list_info[index][2])
				for x in class_list_info[index][4]:
						flag=send_email(class_list_info[index][0],"{}-{}-{}".format(x[1],x[2],time.strftime("%Y-%m-%d %H:%M:%S",\
					time.localtime(x[3]))),"暂未查看")
						if(flag==1):
							print("通知未读，邮件提醒")
							f=open(records_file,"a+")
							f.writelines(["{} {}".format(class_list_info[index][2],x[3])])
				study_class_over_time(s,class_list_info[index][2])
				time.sleep(60)
				cnt=cnt+1
				if(cnt>35):
					print("今天的学习结束")
					break
	except:
		print("崩溃一次")
		continue
	



	


