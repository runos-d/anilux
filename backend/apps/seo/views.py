import json
import re
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponse, HttpResponsePermanentRedirect, JsonResponse, QueryDict
from django.template.loader import render_to_string
from django.views.decorators.http import require_safe

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .service import build_page, site_config
from .navigation import site_navigation


def safe_json(value):
    return json.dumps(value, ensure_ascii=False, default=str).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def content_html(page):
    return render_to_string('seo/content.html', {'page': page})


def uncached(response, robots='noindex,follow'):
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = robots
    return response


@lru_cache(maxsize=4)
def read_shell(filename, mtime):
    return Path(filename).read_text(encoding='utf-8')


def shell():
    filename = Path(settings.SEO_FRONTEND_INDEX)
    if filename.is_file():
        return read_shell(str(filename), filename.stat().st_mtime_ns)
    return '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="app"></div></body></html>'


def projection(request, path, query):
    try:
        return build_page(request, path, query)
    except (ValueError, TypeError):
        from .service import error_page
        return build_page(request, '/__not_found__', QueryDict())


def normalized_redirect_target(path, query, redirect=''):
    """Build one-hop redirects without duplicate or tracking-only query URLs."""
    parsed = urlsplit(redirect or path)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    pairs.extend((key, value) for key, values in query.lists() for value in values)
    cleaned = []
    seen = set()
    for key, value in pairs:
        if key == 'page' and value == '1':
            continue
        if key.startswith('utm_') or key in {'gclid', 'yclid'}:
            continue
        if key not in seen:
            cleaned.append((key, value))
            seen.add(key)
    return urlunsplit(('', '', parsed.path, urlencode(cleaned, doseq=True), ''))


@require_safe
def page_html(request, path=''):
    path = '/' + path
    normalized = re.sub('/+', '/', path).rstrip('/') or '/'
    page = projection(request, normalized, request.GET)
    _, origin, enabled, _ = site_config(request)
    target = normalized_redirect_target(normalized, request.GET, page.redirect)
    foreign_origin = enabled and (request.get_host() != urlsplit(origin).netloc or not request.is_secure())
    normalizable = page.status == 200 or bool(page.redirect)
    if page.redirect or (normalizable and (path != normalized or foreign_origin or request.GET.get('page') == '1')):
        return uncached(HttpResponsePermanentRedirect((origin if enabled else '') + target))
    nonce = getattr(request, 'csp_nonce', '')
    head = render_to_string('seo/head.html', {'page': page, 'json_ld': safe_json(page.schema), 'csp_nonce': nonce})
    payload = asdict(page)
    payload['contentHtml'] = content_html(page)
    footer = render_to_string('seo/footer.html', {'navigation': site_navigation()})
    html = shell()
    html = re.sub(r'<title\b[^>]*>.*?</title>', '', html, flags=re.I | re.S)
    html = re.sub(r'<meta\b[^>]*(?:name=["\'](?:description|robots|twitter:[^"\']+|apple-mobile-web-app-title)["\']|property=["\']og:[^"\']+["\'])[^>]*>', '', html, flags=re.I)
    html = re.sub(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', '', html, flags=re.I)
    html = html.replace('</head>', head + f'<script nonce="{nonce}" id="seo-bootstrap" type="application/json">' + safe_json(payload) + '</script></head>')
    html = re.sub(r'<div id="app">\s*</div>', lambda _: '<div id="app"><main data-seo-main>' + payload['contentHtml'] + '</main>' + footer + '</div>', html)
    html = re.sub(r'<script(?![^>]*\bnonce=)', f'<script nonce="{nonce}"', html, flags=re.I)
    return uncached(HttpResponse(html, status=page.status), page.robots)


@require_safe
@api_view(['GET', 'HEAD'])
@permission_classes([AllowAny])
def page_data(request):
    from urllib.parse import urlsplit, unquote
    value = request.GET.get('path', '/')
    parsed = urlsplit(value)
    if not value.startswith('/') or value.startswith('//') or parsed.netloc or len(value) > 2000:
        return uncached(JsonResponse({'detail': 'Некорректный путь'}, status=400))
    path = unquote(parsed.path).rstrip('/') or '/'
    page = projection(request, path, QueryDict(parsed.query))
    data = asdict(page)
    data['contentHtml'] = content_html(page)
    return uncached(JsonResponse(data), page.robots)


@require_safe
def robots(request):
    _, origin, enabled, _ = site_config(request)
    text = 'User-agent: *\n' + ('Disallow: /\n' if not enabled else 'Disallow: /api/\nDisallow: /ws/\n')
    text += f'Sitemap: {origin}/sitemap.xml\n'
    return uncached(HttpResponse(text, content_type='text/plain; charset=utf-8'))
