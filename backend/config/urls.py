from apps.social.presentation.views.chat_media import public_chat_file_denied
from apps.social.presentation.views.post_media import serve_post_media
from apps.users.presentation.views.profile_media import profile_media

import re

from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.anime.presentation.views.clip_views import ClipCreateView, ClipStatusView
from django.views.generic import TemplateView
from config import feature_flags
from config.health import liveness, readiness
from config.disabled_features import disabled_feature

try:
    from . import views_admin
except ImportError:
    views_admin = None
import time

from config import views_admin
from apps.users.presentation.views.email_webhooks import BrevoTransactionalEventsView

import rest_framework.urlpatterns
rest_framework.urlpatterns.format_suffix_patterns = lambda patterns, **kwargs: patterns



def api_status(request):
    from apps.anime.infrastructure.models.anime import Anime, Genre

    return JsonResponse(
        {
            "status": "ok",
            "message": f"{settings.PROJECT_BRAND_NAME} API работает!",
            "timestamp": time.time(),
            "models": {
                "anime": Anime.objects.count(),
                "genres": Genre.objects.count(),
            },
            "endpoints": {
                "anime": "/api/anime/",
                "playlists": "/api/playlists/",
                "users": "/api/users/",
                "social": "/api/social/",
                "notifications": "/api/notifications/",
            },
        }
    )


from django.views.static import serve as media_serve


def seo_admin_shell(request):
    from apps.seo.views import page_html
    return page_html(request, request.path.lstrip('/'))

urlpatterns = [
    path('health/live/', liveness),
    path('health/ready/', readiness),
    re_path(r"^(?:data/)?media/(?P<name>avatars/.+)$", profile_media),
    re_path(r'^admin/(?:complaints|franchises|kodik-import)/?$',
            seo_admin_shell),
    path('api/application/', include('apps.native_apps.urls')),
    path('api/social/post-media/path/<path:name>', serve_post_media),
    path('media/posts/<path:name>', lambda request, name: serve_post_media(request, 'posts/' + name)),
    path('data/media/posts/<path:name>', lambda request, name: serve_post_media(request, 'posts/' + name)),
    path("admin/", admin.site.urls),
    path("api/status/", api_status),
    path("api/integrations/brevo/transactional-events/", BrevoTransactionalEventsView.as_view()),
    path("api/users/", include("apps.users.presentation.urls")),
    path("api/anime/", include("apps.anime.presentation.urls")),
    path("api/playlists/", include("apps.playlists.presentation.urls")),
    path("api/social/", include("apps.social.presentation.urls")),
    path("api/notifications/", include("apps.notifications.presentation.urls")),
    path("api/studios/", include("apps.studios.presentation.urls")),
    path("api/ideas/", include("apps.ideas.urls")),
    path("api/chats/", include("apps.social.presentation.urls")),
    path("api/admin/run-kodik-import/", views_admin.RunKodikImportView.as_view()),
    path("api/admin/run-jikan-import/", views_admin.RunJikanImportView.as_view()),
    path("api/admin/import-status/", views_admin.AdminImportStatusView.as_view()),
    path("api/admin/stop-import/", views_admin.AdminStopImportView.as_view()),
    path("api/admin/run-franchise-rebuild/", views_admin.AdminRunFranchiseRebuildView.as_view()),
    path("api/admin/run-calendar-sync/", views_admin.AdminRunCalendarSyncView.as_view()),
    path("api/admin/wipe-all/", views_admin.AdminWipeAllView.as_view()),
    path('api/anime/clip/create/', ClipCreateView.as_view(), name='clip_create'),
    path('api/anime/clip/status/', ClipStatusView.as_view(), name='clip_status'),
    path('sw.js', TemplateView.as_view(
        template_name='sw.js',
        content_type='application/javascript'
    ), name='sw'),
    re_path(
        r"^shop-verification-og7k9w1Zma\.txt$",
        lambda r: HttpResponse(
            "shop-verification-og7k9w1Zma", content_type="text/plain"
        ),
    ),
] + [
    re_path(r"^(?:data/)?media/(?:attachments|message_media|scheduled_messages|chat_backups)/(?P<path>.*)$", public_chat_file_denied),
    re_path(
        r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
        media_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
    re_path(
        r"^media/(?P<path>.*)$",
        media_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

if feature_flags.FEATURE_DUBS_ENABLED:
    urlpatterns.insert(0, path("api/dubs/", include("apps.dubs.presentation.urls")))
else:
    urlpatterns.insert(0, re_path(r"^api/dubs(?:/.*)?$", disabled_feature))
if feature_flags.FEATURE_REACTOR_ENABLED:
    urlpatterns.insert(0, path("api/reactor/", include("apps.reactor.presentation.urls")))
else:
    urlpatterns.insert(0, re_path(r"^api/reactor(?:/.*)?$", disabled_feature))

from apps.seo.views import page_html, page_data, robots
from apps.seo.sitemaps import sitemap
urlpatterns += [
    path('api/seo/page/', page_data),
    path('robots.txt', robots),
    path('sitemap.xml', sitemap),
    re_path(r'^sitemap-(?P<section>[a-z]+)-(?P<number>[1-9][0-9]*)\.xml$',
            lambda request, section, number: sitemap(request, section, int(number))),
    re_path(r'^(?P<path>.*)$', page_html),
]
