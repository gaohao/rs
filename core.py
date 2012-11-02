
from types import FunctionType


__all__ = [
    'encoding',
    'registry',
    'method',
    'path',
    'produces',
    'consumes',
    'get',
    'post',
    'put',
    'delete',
]


encoding = 'utf-8' # default encoding.
registry = set()   # set of registered resources.


get_rest_dict = lambda o: getattr(o, '__rest_dict__')
set_rest_dict = lambda o, v: setattr(o, '__rest_dict__', v)
has_rest_dict = lambda o: (get_rest_dict(o)
                    if isinstance(o, RestDict)
                    else hasattr(o, '__rest_dict__'))


class RestDict(dict):
    '''RestDict will contain all notations on resources 
    
    '''
    __slots__ = ()
    __getattr__ = lambda self, k: self.get(k)
    __setattr__ = lambda self, k, v: self.setdefault(k, v)


def rest_api(rest_func):
    
    def rest_actual(resource):
        '''rest_func may be method_actual, path_actual, 
        produces_actual, consumes_actual
            
        '''
        if not isinstance(resource, (type, FunctionType)):
            raise TypeError(
                'unexpected type specified: {0}, must be class or function'
                .format(resource))
        if not has_rest_dict(resource):
            set_rest_dict(resource, RestDict())
            registry.add(resource)
        rest_func(get_rest_dict(resource))
        return resource
    return rest_actual


def method(name):
    @rest_api
    def method_actual(rest_dict):
        rest_dict.method = name
    return method_actual


def path(pattern):
    @rest_api
    def path_actual(rest_dict):
        rest_dict.path = '/' + pattern.strip('/\\').replace('\\', '/')
    return path_actual


def produces(media, producer=None):
    @rest_api
    def produces_actual(rest_dict):
        rest_dict.producer = media.lower(), producer
    return produces_actual


def consumes(media, consumer=None):
    @rest_api
    def consumes_actual(rest_dict):
        rest_dict.consumer = media.lower(), consumer
    return consumes_actual


get     = method('GET')
post    = method('POST')
put     = method('PUT')
delete  = method('DELETE')



#path
#Service = path('/service')(Service)
#path_actual = rest_api(path_actual)
#path_actual = rest_actual
#Service = rest_actual(Service)
#Service=Service