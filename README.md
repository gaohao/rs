rs
==
A Simple RESTful framework for python3  
[![Build Status](https://travis-ci.org/gaohao/rs.png?branch=master,staging,production)](http://travis-ci.org/gaohao/rs)  

How to use:
<pre>
import rs  
@rs.path('/hello')  
@rs.get  
def helloservice(self):  
	return 'hello world!'  
application = rs.application()  
application.run('', 8001, debug=False)  
</pre>
You can try http://localhost:8001/hello  
