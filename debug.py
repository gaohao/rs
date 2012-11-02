


import logging

from functools import wraps


__all__ = [
    'debug',
    'conditional',
    'profiling',
    'log_return',
    'log_params',
    'log_exception',
    'basic_logging',
]


def basic_logging(level=logging.INFO):
    base_fmt = "%(asctime)s  %(module)-1s {0} %(levelname)-5s - %(message)s"
    fmt = base_fmt.format('(%(funcName)-1s:%(lineno)d)'
                          if level < logging.INFO else '')
    formatter = logging.Formatter(fmt, "%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger('rs')
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = 0
    return logger


def debug():
    logger = logging.getLogger(__name__)
    from rs.request import Request as req
    from rs.response import Response as resp
    from rs.resource import Resource as rsrc
    from rs.application import WSGIApplication as app
    from rs.context import Context as ctx
    req.__str__ = format_request
    resp.__str__ = format_response
    rsrc.__str__ = format_resource
    app.complete_response = (
        log_params('response', logger=logger)
            (app.complete_response)
    )
    app.complete_request = (
        log_return(logger=logger)
            (app.complete_request)
    )
    __del__ = lambda self: logger.debug('%r deleted.', self)
    req.__del__ = resp.__del__ = rsrc.__del__ = ctx.__del__ = __del__
    app.__call__ = profiling(app.__call__)

    
def profiling(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        import pstats, cProfile
        profile = cProfile.Profile()
        returned = profile.runcall(func, *args, **kwargs)
        stats = pstats.Stats(profile)
        stats.strip_dirs().sort_stats('cumulative', 'calls').print_stats()
        return returned
    return wrapped

    
def conditional(condition, decorator):
    return lambda func: decorator(func) if condition else func


def log_return(**log):
    def wrapper(func):
        logger = log.get('logger', logging.root)
        level = log.get('level', logging.DEBUG)
        @wraps(func)
        def wrapped(*args, **kwargs):
            returned = func(*args, **kwargs)
            logger.log(level, returned)
            return returned
        _update_wrapped_varnames(wrapped, func)
        return wrapped
    return wrapper


def log_params(*params, **log):
    def wrapper(func):
        logger = log.get('logger', logging.root)
        level = log.get('level', logging.DEBUG)
        @wraps(func)
        def wrapped(*args, **kwargs):
            for p in params:
                if p in kwargs:
                    logger.log(level, kwargs.get(p))
                else:
                    co_varnames = getattr(func, '__co_varnames__',
                                          func.__code__.co_varnames)
                    if p in co_varnames:
                        i = co_varnames.index(p)
                        if i < len(args):
                            logger.log(level, args[i])
            return func(*args, **kwargs)
        _update_wrapped_varnames(wrapped, func)
        return wrapped
    return wrapper


def log_exception(*exceptions, **log):
    def wrapper(func):
        logger = log.get('logger', logging.root)
        level = log.get('level')
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if type(e) in exceptions:
                    if not level:
                        logger.exception(e)
                    else:
                        logger.log(level, e)
                raise
        _update_wrapped_varnames(wrapped, func)
        return wrapped
    return wrapper


def _update_wrapped_varnames(wrapped, func):
    setattr(wrapped, '__co_varnames__',
            getattr(func, '__co_varnames__', func.__code__.co_varnames))


def format_request(request):
    return """
{klass}: {{
    method: {0},
    uri: {1},
    version: {2},
    headers: {3}
}}""".format(request.method,
             request.uri.path,
             request.version,
             request.headers,
             klass=request.__class__)


def format_response(response):
    return """
{klass}: {{
    status: {0},
    headers: {1}
}}""".format(response.status,
             response.headers,
             klass=response.__class__)


def format_resource(resource):
    return """
{klass}: {{
    method: {0},
    path: {1},
    pattern: {2},
    consumer: {3},
    provider: {4},
    target: {5},
    type: {6}
}}""".format(resource.method,
             resource.path,
             resource.pattern and resource.pattern.pattern,
             resource.consumer,
             resource.producer,
             resource.target,
             resource.type,
             klass=resource.__class__)