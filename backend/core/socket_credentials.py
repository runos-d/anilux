"""Keep browser bearer credentials out of request URLs and proxy error logs."""
from urllib.parse import parse_qs
from django.conf import settings

PROTOCOL = 'animecore.v2'


def socket_token(scope):
    for protocol in scope.get('subprotocols', ()):
        if protocol.startswith('auth.'):
            return protocol[5:] or 'invalid'
    if not getattr(settings, 'WS_ALLOW_QUERY_TOKEN', True):
        return None
    query = scope.get('query_string', b'')
    if isinstance(query, bytes):
        query = query.decode(errors='ignore')
    return parse_qs(query).get('token', [None])[0]


def accepted_protocol(scope):
    return PROTOCOL if PROTOCOL in scope.get('subprotocols', ()) else None
