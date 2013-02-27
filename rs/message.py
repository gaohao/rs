


from collections import namedtuple

from rs.core import RestDict, encoding as default_encoding


__all__ = [
    'uri',
    'entity',
    'set_headers',
    'set_entity',
    'parse_header',
    'parse_media',
    'parse_accept',
]


uri = namedtuple('uri', 'path, query')


def entity(entity, encoding=None):
    encoding = encoding or default_encoding
    try:
        if not isinstance(entity, str):
            entity = str(entity, encoding=encoding)
        #return entity.encode(encoding)
        return entity
    except  UnicodeDecodeError:
        return entity


def set_headers(message, headers):
    if headers:
        for k,v in headers.items(): # items() is used due to rfc822.Message compatibility
            message.headers[k.lower()] = v


def set_entity(message, entity_, media=None):
    #message -> Response
    if entity_ is not None:
        media = parse_media(media or 'application\octet-stream')
        message.headers['content-type'] = \
        media.header if media.charset else combine_header(media.value,
                                                          ('charset',
                                                           default_encoding))
        message.headers['content-length'] = str(len(entity_))
        message.entity = entity(entity_, media.charset or default_encoding)


def parse_header(header):
    t, p = header.strip().split(';', 1) if ';' in header else (header, None)
    params = p.strip().split(';') if p else []
    parsed = [('value', t.strip()), ('header', header)]
    parsed.extend([p.strip().split('=', 1) for p in params])
    return RestDict(parsed)


def parse_media(media, _parser=parse_header):
    parsed = _parser(media)
    parsed.update(zip(('type', 'subtype'), parsed.value.strip().split('/')))
    return parsed


def parse_accept(accept, _parser=parse_media):
    def sort_key(p):
        return float(p.q) if p.q else 1.0, len(p.value), len(p)
    parsed = map(_parser, accept.split(','))
    return sorted(parsed, key=sort_key, reverse=True)


def combine_header(value, *params):
    return value + ''.join(';{0}={1}'.format(*p) for p in params)