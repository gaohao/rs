

import re

from inspect import getfullargspec
from types import FunctionType

from rs.core import has_rest_dict, get_rest_dict



__all__ = [
    'Resource',
    'build_all',
]


class Resource(object):
    
    def __init__(self):
        '''init the Resource
        
        '''
        #will be copied from __rest_dict__
        self.method = None #acceptable request method
        self.path = None
        self.consumer = None
        self.producer = None
        
        self.pattern = None
        self.target = None #target function to be invoke
        self.host = None #host of the target
        
        self._fullargspec = None # a list of argument names of target
        self._args_defs = {} #default params and its values of target

    def __hash__(self):
        return hash(self.target)


class ResourceBuilder(object):
    '''
        
    '''
    def __init__(self, buildobj, _extends=None):
        if not isinstance(buildobj, (type, FunctionType)):
            raise TypeError(
                'unexpected type specified: {0}, type must be class or function'
                .format(buildobj))
        self.buildobj = buildobj
        self._path_chain = []
        if _extends:
            self._path_chain.extend(_extends)

    def build(self):
        if isinstance(self.buildobj, type):
            return self.build_resources()
        elif isinstance(self.buildobj, FunctionType) and has_rest_dict(self.buildobj):
            return [self.build_resource(target=self.buildobj)]
        return []

    def build_resources(self):
        resources = []
        if has_rest_dict(self.buildobj):
            self._path_chain.append(get_rest_dict(self.buildobj))# search chain
            
        for v in vars(self.buildobj).values():
            if isinstance(v, type):
                resources.extend(ResourceBuilder(v,
                                    self._path_chain).build_resources())
            elif isinstance(v, FunctionType):
                if has_rest_dict(v):
                    resources.append(self.build_resource(target=v,
                                                         host=self.buildobj))
        return resources

    def build_resource(self, target, host=None):
        resource = Resource()
                
        for k,v in get_rest_dict(target).items():
            if k in resource.__dict__ and not resource.__dict__.get(k) and k != 'path':
                resource.__dict__[k] = v
        
        #build path
        resource.path='/'
         
        self._path_chain.append(get_rest_dict(target))              #add tail
        if self._path_chain is not []:
            for rest_dict in self._path_chain:
                if rest_dict.path:
                    resource.path = (resource.path.rstrip('/') +    #remove the tailing letter '/' 
                                 '/' +
                                 rest_dict.path.strip('/'))
        self._path_chain.remove(get_rest_dict(target))              #remove tail
            
        resource.target = target
                
        params = dict(('{{{0}}}'.format(p),
                       '(?P<{0}>.+)'.format(p)
                      ) for p in re.findall(r'''\{
                                            (.+?)    #groups
                                            \}''', resource.path, re.VERBOSE))
        
        pattern = resource.path
        for k,v in params.items():
            pattern = re.sub(k, v, pattern)
                    
        resource.pattern = re.compile(r'^{0}$'.format(pattern.strip('/'))) #match exactly the path
        
        if host:
            resource.host = host
            
        resource._fullargspec = getfullargspec(resource.target)
        if resource._fullargspec.defaults:
            tmp = resource._fullargspec
            resource._args_defs = dict(zip(tmp.args[-(len(tmp.defaults)):], tmp.defaults))
        
        return resource

def build_all(resources):
    resources = set(resources)
    
    #Select the top level class. Top means at the root of 'path' tree
    for c in [c for c in resources if isinstance(c, type)]:
        for v in [v for v in vars(c).values()
                  if isinstance(v, (type, FunctionType))]:
            if has_rest_dict(v):
                resources.discard(v)

    resources = sum(map(lambda resource : ResourceBuilder(resource).build(), 
                        resources),
                         [])
    return resources