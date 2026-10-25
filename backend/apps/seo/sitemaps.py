import math
from xml.etree.ElementTree import Element, SubElement, tostring

from django.http import HttpResponse
from django.views.decorators.http import require_safe

from .models import SeoHub, SeoOverride
from .service import (visible_anime, anime_path, profile_path, site_config, build_page,
                      indexable_profiles, indexable_posts, indexable_playlists)
from .views import uncached
from django.http import QueryDict

NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
SECTIONS = {'pages': 100, 'anime': 1000, 'profiles': 1000, 'posts': 1000, 'playlists': 1000, 'hubs': 50}


def query(section):
    if section == 'pages':
        from .navigation import site_navigation
        return ['/', '/anime', '/anime/browse', '/anime/franchises', '/contacts', '/ideas'] + [
            item['path'] for item in site_navigation()['documents'] if item.get('published')]
    if section == 'anime':
        return visible_anime().only('id', 'slug', 'updated_at').order_by('pk')
    if section == 'profiles':
        return indexable_profiles().only('id', 'nickname', 'bio').order_by('pk')
    if section == 'posts':
        return indexable_posts().only('id', 'public_id', 'edited_at', 'published_at', 'created_at', 'text').order_by('pk')
    if section == 'playlists':
        return indexable_playlists().only('id', 'updated_at', 'description').order_by('pk')
    return SeoHub.objects.exclude(path__in=query('pages')).order_by('path')


def candidate_count(candidates):
    return len(candidates) if isinstance(candidates, list) else candidates.count()


def xml(root):
    return uncached(HttpResponse(tostring(root, encoding='utf-8', xml_declaration=True), content_type='application/xml; charset=utf-8'))


@require_safe
def sitemap(request, section=None, number=1):
    _, origin, enabled, config = site_config(request)
    if section is None:
        root = Element('sitemapindex', xmlns=NS)
        if enabled:
            for name, size in SECTIONS.items():
                for page in range(1, max(1, math.ceil(candidate_count(query(name)) / size)) + 1):
                    entry = SubElement(root, 'sitemap')
                    SubElement(entry, 'loc').text = f'{origin}/sitemap-{name}-{page}.xml'
        return xml(root)
    if section not in SECTIONS or number < 1:
        return uncached(HttpResponse(status=404))
    root = Element('urlset', xmlns=NS)
    if not enabled:
        return xml(root)
    size = SECTIONS[section]
    qs = query(section)
    if number > max(1, math.ceil(candidate_count(qs) / size)):
        return uncached(HttpResponse(status=404))
    overrides = {row.path: row for row in SeoOverride.objects.all()}
    for obj in qs[(number - 1) * size:number * size]:
        modified = None
        if section == 'anime':
            path, modified = anime_path(obj), obj.updated_at
        elif section == 'profiles':
            path = profile_path(obj)
        elif section == 'posts':
            path, modified = f'/post/{obj.public_id}', obj.edited_at or obj.published_at or obj.created_at
        elif section == 'playlists':
            path, modified = f'/playlist/{obj.pk}', obj.updated_at
        elif section == 'pages':
            page = build_page(request, obj, QueryDict())
            if not page.indexable or page.redirect or page.status != 200:
                continue
            path, modified = page.path, page.modified
        else:
            page = build_page(request, obj.path, QueryDict())
            if not page.indexable or page.redirect or page.status != 200:
                continue
            path, modified = obj.path, max(filter(None, [page.modified, obj.lastmod]), default=None)
        override = overrides.get(path)
        if override and override.noindex:
            continue
        modified = max(filter(None, [modified, override.updated_at if override else None, config.updated_at if config else None]), default=None)
        entry = SubElement(root, 'url')
        SubElement(entry, 'loc').text = origin + path
        if modified:
            SubElement(entry, 'lastmod').text = modified.isoformat()
    return xml(root)
