import requests as Re
import execjs as jsexe
import re
import time
from smtp import send_email
from html_escape_sequence import escape2normal
user=""
pd=""#你的账号密码
rsa_key=""
lt_str=""
execution=""
vatify_code=""
s=Re.Session()
login_flag=0
class_list_info=[]
pwd="/root/lazy_student_assist/"
records_file=pwd+"inform_records.dat"
log_file=pwd+"log.dat"
column_type2name={"study":"课程学习","discuss":"答疑讨论"}
#python参数传递 永远是传递指针而不是新分配空间 再拷贝，因此对函数内部的参数进行修改，会修改传入的变量
#python变量作用域 全局变量在函数中使用时，只能读，不能写（改） 需要写，就要在函数里声明 global 全局变量名


#log函数 level等级越低 记录越不重要
def write_log(log,level=0):
	f=open(log_file,"a+")
	f.write("{} {} {}\n".format(str(level),str(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))),log))
	f.close()
#以下函数从本地读取帖子 如果有，返回元组，如果没有返回空元组
def syntax_class_forum(forumid):
	f=open(records_file,"r")
	lines=f.readlines()
	f.close()
	ret=[]
	for x in lines:
		result=re.match("(forum )([\d]+)( )([\S]+?)( )([\d]+)( )(.+)",x)
		if(result):
			if(int(forumid)==int(result[2])):
				ret.append(result[2])
				ret.append(result[4])
				ret.append(result[6])
				ret.append(result[8])
				break
	return ret
#以下函数读取records.dat,查看各个column的id，如果没有就解析网页，获取id
def syntax_class_column_id(session,column_type,classid):
	f=open(records_file,"r")
	lines=f.readlines()
	f.close()
	ret=-1
	for x in lines:
		#study_column_id 10722 7753
		result=re.match("("+column_type+"_column_id )([\d]+)( )([\d]+)",x)
		if(result):
			if(int(result[2])==int(classid)):
				ret=int(result[4])
				break
	if(ret==-1):
		res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/layout/newpage/index.jsp",\
		params={"courseId":str(classid)})
		ctx=re.compile("(columnId=)([\d]+)([\s\S]{20,160})(<span>)(.*?)(</span>)")
		result=ctx.findall(res.text)
		for x in result:
			if(column_type2name[column_type]==str(x[4])):
				f=open(records_file,"a+")
				f.write("{} {} {}\n".format(column_type+"_column_id",str(classid),str(x[1])))
				f.close()
				ret=int(x[1])
				break
	return ret
#该函数返回上个月1号这个时间的时间戳
def last_n_day_timestamp(n):
	return (int(time.time())-24*60*60*n)
#以下函数读取records.dat,查看class对应的最后一次已读通知的时间戳，如果没有记录就使用上个月1号的时间戳
def syntax_class_records_last_time(select_type,classid):
	f=open(records_file,"r")
	lines=f.readlines()
	f.close()
	last_time_rec=last_n_day_timestamp(30)
	for x in lines:
		result=re.match("("+select_type+" )([\d]+)( )(.+)",x)
		if(result):
			class_id=result[2]
			last_time_str=result[4]
			if(class_id==classid and int(last_time_str)>last_time_rec):
				last_time_rec=int(last_time_str)
				break
	return last_time_rec
#以下函数读通知内容
def get_info_content(session,informid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/common/inform/message_content.jsp",params={"nid":str(informid)})
	origin_content=re.search("(id=.*?_content.*?value=')(.*?)(')",res.text)
	if(origin_content):
		origin_content=origin_content[2]
	else:
		origin_content="暂无内容"
	origin_content=escape2normal(origin_content)
	return origin_content
#以下函数获取登陆cookie
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
	f=open(pwd+"des.js","r")
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
	# if(res.text.find("id=\"vali\"")>0):
	# 	print("要输入验证码！")
	# 	write_log("此次登录需要验证码")
	# 	img_src="http://zhlgd.whut.edu.cn/tpass/code"#暂时是不变的 懒得解析了
	# 	res=session.get(img_src)
	# 	f=open(pwd+"vatify.jpeg","wb+")
	# 	f.write(res.content)
	# 	f.close()
	# 	vatify_code=str(input("请查看并输入验证码！保存在/home/lsm/vatify.jpeg"))
	# 	data_to_send["code"]=vatify_code
	res=session.post("http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fzhlgd.whut.edu.cn%2Ftp_up%2F",data=data_to_send)
	if(len(res.history)>0 and res.text.find("在线人数")>0):
		print("login success")
		write_log("login success")
		login_flag=1
	else:
		print("login fail")
		write_log("login success")
#此函数浏览并点赞未读帖子 class_list_info[index][5]是未读forum列表
def view_and_support_unread_forum(session,class_list_info,index):
	for x in class_list_info[index][5]:
		res=session.get("http://jxpt.whut.edu.cn:81/meol/homepage/threadAction.do",params={"threadid":str(x[0])})
		res=session.post("http://jxpt.whut.edu.cn:81/meol/common/faq/forumnSupport_do.jsp",params={"threadId":str(x[0])})
		if(res.text.find("已支持")!=-1):
			write_log("已读已点赞帖子:{} {} {}".format(x[0],x[1],x[3]))
			f=open(records_file,"a+")
			f.write("forum {} {} {} {}\n".format(x[0],x[1],x[2],x[3]))
			f.close()
		elif(res.text.find("不能重复支持")!=-1):
			f=open(records_file,"a+")
			f.write("forum {} {} {} {}\n".format(x[0],x[1],x[2],x[3]))
			f.close()
#此函数传入三个参数 1会话session,2课程id,3学习资源所在的栏目名字
def view_class_column_page(session,classid,column_type):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/layout/newpage/index.jsp",\
		params={"courseId":str(classid)})
	columnid=syntax_class_column_id(session,column_type,classid)
	res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/course_column_preview_transfer.jsp",\
		params={"tagbug":"client","columnId":str(columnid)})
	return res.text
#以下函数增加学习时间
def study_class_over_time(session,classid):
	res=session.post("http://jxpt.whut.edu.cn:81/meol/lesson/onlinetime_listener.jsp",\
		data={"lessId":str(classid)})
	if(res.text.find("success\",\"status\":0")>0):
		write_log("学习一分钟，发送请求")
#以下函数获取课程学习时间
def syntax_study_info(study_html_text):
	ret=[]
	study_time=re.search("(本课程网络学习总时长[\S\s]*?needstar\">[\s]+)([\d]+)",study_html_text)[2]
	ret.append(study_time)
	return ret
#以下函数获取学习情况
def get_study_info(session,classid,uid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/common/newscoremanagement/stu_course_detail.jsp",\
		params={"lid":str(classid),"uid":str(uid)})
	return syntax_study_info(res.text)
#以下函数填写个人所有课程信息数组 每门课程：name teachername id class_inform class_discuss
def class_syntax(class_li_text):
	ret=[]
	#<span class='realname'>张进</span>
	#courseId=
	class_name=re.search("(title[\S\s]*?>[\S\s]*?>[\s]*)([\S]*)",class_li_text)[2]
	teacher_name=re.search("(realname.*?>)([\S]*)(</span)",class_li_text)[2]
	class_id=re.search("(courseId=)([\d]+)",class_li_text)[2]
	class_inform=[]
	class_discuss=[]
	ret.append(class_name)
	ret.append(teacher_name)
	ret.append(class_id)
	ret.append(class_inform)
	ret.append(class_discuss)
	return ret
#此函数直接填充class_list_info数组，每个数组代表一门课 每门课有 name teachername id info discuss
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
			write_log("编号 {}:{}".format(index,str(x)))
#以下函数获取所有未记录的帖子 保存在records.dat文件里
def get_class_discuss(session,classid):
	discuss_html=view_class_column_page(session,classid,"discuss")
	ctx=re.compile("(<tr>[\s\S\r\n]*?href.*?threadid=)([\d]+)([\s\S\r]*?title=\")(.+)(\"[\S\s]*?<td.*?>[\s]*)(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)([\s\S]*?<td.*?>[\s]*)([\S]*)")
	result=ctx.findall(discuss_html)
	unread_discuss_list=[]
	if(result):
		for x in result:
			single_forum=[]
			forum_id=x[1]
			forum_title=x[3]
			forum_timestamp=int(time.mktime(time.strptime(x[5],"%Y-%m-%d %H:%M:%S")))
			forum_sender=x[7]
			single_forum.append(forum_id)
			single_forum.append(forum_title)
			single_forum.append(forum_timestamp)
			single_forum.append(forum_sender)
			if(syntax_class_forum(forum_id)==[]):
				unread_discuss_list.append(single_forum)
	return unread_discuss_list
			#print(x[1],x[3],x[5],x[7])
#以下函数获取未读通知列表（未读时间保存在records.dat里 如果没有记录就默认是上个月1号）
def get_class_inform(session,classid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/common/inform/index_stu.jsp",\
		params={"tagbug":"client","s_order":"0","lid":str(classid),"strStyle":"new06"})
	ctx=re.compile("(<tr>[\s\S]*?<td>[\s\S]*?</td>[\s\S]*?</tr>)")
	class_inform_text=ctx.findall(res.text)
	class_unread_inform_list=[]
	index=0
	for x in class_inform_text:
		single_inform=[]
		informid=re.search("(jsp\?nid=)([\d]+)",x)[2]
		#class="align_c">罗先平
		inform_time=re.search("(<td[\s\S]*?\"align_c\">)(.*?)(\n[\s\S]*?\"align_c\">)(.*?)(\n)",x)[2]
		inform_time=int(time.mktime(time.strptime(inform_time,"%Y-%m-%d %H:%M:%S")))
		if(inform_time>syntax_class_records_last_time("inform",classid)):
			inform_title=re.search("(title=\")([\S\s]*?)(\"\n *onClick)",x)[2]
			inform_sender=re.search("(<td[\s\S]*?\"align_c\">)(.*?)(\n[\s\S]*?\"align_c\">)(.*?)(\n)",x)[4]
			inform_content=get_info_content(session,informid)
			single_inform.append(informid)
			single_inform.append(inform_title)
			single_inform.append(inform_sender)
			single_inform.append(inform_time)
			single_inform.append(inform_content)
			class_unread_inform_list.append(single_inform)
			index=index+1
	return class_unread_inform_list
#以下函数发送邮件提醒未读通知
def send_unread_info(class_list_info,index):
	for x in class_list_info[index][4]:
			flag=send_email(class_list_info[index][0],"{}-{}-{}".format(x[1],x[2],time.strftime("%Y-%m-%d %H:%M:%S",\
				time.localtime(x[3]))),x[4],"html")
			if(flag==1):
				write_log("通知未读，邮件提醒")
				f=open(records_file,"a+")
				f.write("{} {} {}\n".format("inform",class_list_info[index][2],x[3]))
				f.close()
#以下更新未读通知列表
def update_unread_list(session,class_list_info,index):
	class_list_info[index][4]=get_class_inform(session,class_list_info[index][2])
	write_log("更新未读通知列表："+str(class_list_info[index][4]))
#以下更新未读帖子列表
def update_unread_discuss(session,class_list_info,index):
	class_list_info[index][5]=get_class_discuss(session,class_list_info[index][2])
	write_log("更新未读讨论贴列表："+str(class_list_info[index][5]))
##
##以下是程序主线程##
class_list_info=[]
login_index(s)
get_all_class_info(s)
index=int(input("请选择一个课程自动学习（输入对应的数字编号）:"))
update_unread_list(s,class_list_info,index)
view_class_column_page(s,class_list_info[index][2],"study")
update_unread_discuss(s,class_list_info,index)
while(1):
	time.sleep(20)
	try:
		update_unread_list(s,class_list_info,index)
		update_unread_discuss(s,class_list_info,index)
		send_unread_info(class_list_info,index)
		now_tuple=time.localtime(time.time())
		#每天到指定时刻开始增加学习时间并且给帖子点赞
		if(int(now_tuple[3])==22 and int(now_tuple[4])>8):
			#刷新登陆状态
			write_log("到时间了开始学习")
			rsa_key=""
			lt_str=""
			execution=""
			vatify_code=""
			s=Re.Session()
			login_flag=0
			class_list_info=[]
			login_index(s)
			get_all_class_info(s)
			update_unread_list(s,class_list_info,index)
			update_unread_discuss(s,class_list_info,index)
			view_class_column_page(s,class_list_info[index][2],"study")
			view_and_support_unread_forum(s,class_list_info,index)
			cnt=0
			while(1):
				update_unread_list(s,class_list_info,index)
				send_unread_info(class_list_info,index)
				study_class_over_time(s,class_list_info[index][2])
				time.sleep(60)
				cnt=cnt+1
				if(cnt>35):
					write_log("今天的学习结束")
					break
	except Exception as e:
		write_log(str(e))
		write_log("崩溃一次")
		continue

	



	


