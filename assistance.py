import requests as Re
import execjs as jsexe
import re
import time
def view_class_index_page(session,classid):
	res=session.get("http://jxpt.whut.edu.cn:81/meol/jpk/course/layout/newpage/index.jsp",\
		params={"courseId":str(classid)})
	#menuUrl('0','73837','课程学习','1',$(this))
	columnid=re.search("(menuUrl.*?,')([\d]*)(','课程学习)",res.text)[2]
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
user="264953"
pd="114181"
rsa_key=""
lt_str=""
execution=""
vatify_code=""
s=Re.Session()
res=s.get("http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fjxpt.whut.edu.cn%3A81%2Fmeol%2Fhomepage%2Fcommon%2Fsso_login.jsp")
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
#print(res.text)
if(res.text.find("id=\"vali\"")>0):
	print("要输入验证码！")
	img_src="http://zhlgd.whut.edu.cn/tpass/code"#暂时是不变的 懒得解析了
	res=s.get(img_src)
	f=open("/home/lsm/vatify.jpeg","wb+")
	f.write(res.content)
	f.close()
	vatify_code=str(input("请查看并输入验证码！保存在/home/lsm/vatify.jpeg"))
	data_to_send["code"]=vatify_code
res=s.post("http://zhlgd.whut.edu.cn/tpass/login?service=http%3A%2F%2Fzhlgd.whut.edu.cn%2Ftp_up%2F",data=data_to_send)
login_flag=0
if(len(res.history)>0 and res.text.find("在线人数")>0):
	print("login success")
	login_flag=1
else:
	print("login fail")
#登陆之后的事情
class_list_info=[]
if(login_flag==1):
	#获取课程列表
	res=s.get("http://jxpt.whut.edu.cn:81/meol/welcomepage/student/course_list_v8.jsp")
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
	index=int(input("请选择一个课程自动学习（输入对应的数字编号）:"))
	view_class_index_page(s,class_list_info[index][2])
	while(1):
		study_class_over_time(s,class_list_info[index][2])
		time.sleep(60)
		

	


