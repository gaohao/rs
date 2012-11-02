from rs.response import Response
from rs.status import OK, NO_CONTENT, BAD_REQUEST
from rs.error import Error
from rs.message import set_entity, set_headers


__all__ = [
    'Context',
]

class context_property(property):

    def __init__(self, fget, *args, **kwargs):
        property.__init__(self, fget)
        self.args, self.kwargs = args, kwargs

    def __bool__(self):
        return False

    def __call__(self, *args, **kwargs):
        obj = type(self).__new__(self.__class__)
        obj.__init__(self.fget, *args, **kwargs)
        return obj

    def __get__(self, context, cls=None):
        if context is None:
            return self
        return self.fget(context, *self.args, **self.kwargs)

class application_property(property):

    def __init__(self, fget):
        property.__init__(self, fget)#fget is the method which @application_property
        self.cache = {}

    def __get__(self, context, cls=None):
        if context is None:
            return self
        if context not in self.cache:
            self.cache[context] = self.fget(context)
        return self.cache[context]

    def __delete__(self, context):
        if context in self.cache:
            del self.cache[context]
        

class Context(object):

    def __init__(self, application, request):
        """

        """
        self._app = application
        self._request = request
        
        resource, params =  application.resources_manager.get_resource(request)
        self._resource = resource
        self._params = params
        
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        del self.instances
        del self.resources
        
    def get_response(self):
        result = self.resource.target(**dict(self.get_target_params()))
        if result is None:
            response = Response(NO_CONTENT)
        elif isinstance(result, tuple):
            response = self.make_response(*result)
        elif not isinstance(result, Response):
            response = self.make_response(result)
        else:
            response = result
        return response
    

    def make_response(self, entity, status=None, headers=None):
        response = Response(status or OK)
        media = None
        if self.resource.producer:
            media, produce = self.resource.producer
            entity = produce(entity) if produce else entity
        set_entity(response, entity, media)
        set_headers(response, headers)
        return response

    def get_target_params(self):
        for i, arg in enumerate(self.resource._fullargspec.args):
            try:
                if i == 0 and self.resource.host:
                    yield arg, self.instances[self.resource.host] #call instances
                elif isinstance(self.resource._args_defs.get(arg), context_property):
                    yield arg, self.resource._args_defs[arg].__get__(self)
                elif arg in self.params.path:
                    yield arg, self.params.path[arg]
                elif arg in self.params.query:
                    yield arg, self.params.query[arg]
                elif arg in self.params.form:
                    yield arg, self.params.form[arg]
                elif arg in self.resource._args_defs:
                    yield arg, self.resource._args_defs[arg]
                else:
                    raise Error(BAD_REQUEST)
            except ValueError:
                raise Error(BAD_REQUEST)

    @context_property
    def entity(self):
        entity = self._request.entity
        if entity is not None and self._resource.consumer:
            media, consume = self._resource.consumer
            if consume:
                entity = consume(entity)
        return entity

    @context_property
    def request(self):
        return self._request

    @context_property
    def uri(self):
        return self._request.uri

    @context_property
    def alias(self, *aliases, **kwargs):
        for dict in (self._params.path,
                     self._params.query,
                     self._params.form):
            for alias in aliases:
                if alias in dict:
                    return dict[alias]
        if 'default' not in kwargs:
            raise ValueError('None of {0} values found'.format(aliases))
        return kwargs['default']

    @application_property
    def resources(self):
        return self._app.resources_manager #TODO: MAYBE CHANGED

    @application_property
    def instances(self):
        return self._app.instances_manager  #_app is application

    @property
    def params(self):
        return self._params

    @property
    def resource(self):
        return self._resource
