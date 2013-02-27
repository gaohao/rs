import rs
@rs.path('/hello')
@rs.get
def helloservice(self):
    return 'hello world!'
application = rs.application()
application.run('', 8001, debug=False)
