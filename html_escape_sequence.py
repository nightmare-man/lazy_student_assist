def escape2normal(escape_str):
	ret=escape_str.replace("&lt;","<")
	ret=ret.replace("&gt;",">")
	ret=ret.replace("&nbsp;"," ")
	ret=ret.replace("&amp;","&")
	ret=ret.replace("&quot;","\"")
	return ret
