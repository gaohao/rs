

class Response(object):

    def __init__(self, status=None):
        self.status  = status
        self.headers = {}
        self.entity = None