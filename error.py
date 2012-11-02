

from rs.response import Response


__all__ = [
    'Error',
]


class Error(Response, Exception):
    pass