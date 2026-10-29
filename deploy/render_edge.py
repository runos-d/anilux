"""Render the existing media/SEO-aware nginx configuration for private app nodes."""
import argparse
import ipaddress
from pathlib import Path
import re


def private_endpoint(value):
    host, port = value.rsplit(':', 1)
    address = ipaddress.ip_address(host.strip('[]'))
    networks = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '100.64.0.0/10', 'fc00::/7')
    if not any(address.version == block.version and address in block
               for block in map(ipaddress.ip_network, networks)):
        raise ValueError('Upstreams must use a private/VPN address')
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError('Invalid upstream port')
    return f'[{address}]:{int(port)}' if address.version == 6 else f'{address}:{int(port)}'


def render(domain, upstreams):
    if not re.fullmatch(r'(?=.{1,253}$)[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', domain):
        raise ValueError('Use a plain DNS domain without a scheme, path or port')
    endpoints = list(dict.fromkeys(private_endpoint(value) for value in upstreams))
    if not endpoints:
        raise ValueError('At least one app node is required')
    source = (Path(__file__).resolve().parents[1] / 'frontend/nginx.conf').read_text(encoding='utf-8')
    source = source.replace('worker_processes auto;', 'worker_processes 1;').replace('worker_connections 16384;', 'worker_connections 32768;')
    old = '        server backend:8000 resolve;'
    assert source.count(old) == 1, 'Review the upstream template before rendering'
    source = source.replace(old, '        least_conn;\n' + '\n'.join(f'        server {endpoint} max_fails=2 fail_timeout=5s;' for endpoint in endpoints) + '\n        keepalive 64;')
    source = source.replace('        listen 80;\n        server_name localhost;',
        f'        listen 443 ssl;\n        http2 on;\n        server_name {domain};\n'
        '        ssl_certificate /etc/nginx/tls/fullchain.pem;\n'
        '        ssl_certificate_key /etc/nginx/tls/privkey.pem;\n'
        '        ssl_protocols TLSv1.2 TLSv1.3;\n'
        '        ssl_session_cache shared:TLS:10m;\n        ssl_session_timeout 1d;')
    redirect = f'''    server {{
        listen 80;
        server_name {domain};
        location = /health {{ access_log off; return 200; }}
        location / {{ return 301 https://{domain}$request_uri; }}
    }}
'''
    source = source.replace('    server {\n        listen 443', redirect + '    server {\n        listen 443', 1)
    # Reuse HTTP upstream connections. The websocket location sets Upgrade separately.
    source = source.replace('            proxy_pass http://backend;\n            proxy_set_header Host',
        '            proxy_pass http://backend;\n            proxy_http_version 1.1;\n            proxy_set_header Connection "";\n            proxy_set_header Host')
    return source


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', required=True)
    parser.add_argument('--upstream', action='append', required=True, help='Private app IP:8000; repeat per node')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        config = render(args.domain, args.upstream)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(config, encoding='utf-8', newline='\n')
    print(f'Edge configuration written to {args.output}')
