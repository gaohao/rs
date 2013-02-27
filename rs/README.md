rs
==
A Simple RESTful framework

How to use:  
import rs  
@rs.path('/hello')  
@rs.get  
def helloservice(self):  
  return 'hello world!'  
application = rs.application()  
application.run('', 8001, debug=False)  

You can try http://localhost:8001/hello  
