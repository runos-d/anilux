from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.anime.presentation.views.catalog_search_views import attachment_anime_search
from apps.anime.presentation.views.admin_catalog_views import (
    AdminFranchiseViewSet, AdminAnimeSearch, CatalogOptions, CatalogRules, CatalogHidden,
)

from apps.anime.presentation.views.anime_views import (
    AnimeViewSet,
    GenresViewSet,
    FranchiseViewSet,
    AnnouncementViewSet,
    SearchAPIView,
    ParserStatusAPIView,
    UpdatesAPIView,
    KodikSearchCandidatesView,
    KodikImportView,
    KodikFiltersView,
    KodikTranslationsView,
    KodikPlayerView,
    CustomDubListView,
    CustomDubDetailView,
    HomeAPIView,
    PersonalizedRecommendationsView,
    AnimeEpisodeNotificationView,
    RandomAnimeView,
    CurrentlyWatchingView,
    UserActiveTabView,
    EpisodeProgressView,
    EpisodeProgressUndoView,
    WatchHistoryView,
    WatchHistoryItemView,
    AnimeThemesView,
    KodikVideoUrlView,
    KodikClipDownloadView,
    AdminTodayAddedAnimeView,
    CatalogSettingsView,
    CalendarView,
    KodikUserAddView,
    KodikMyRequestsView,
)
from apps.anime.presentation.views.catalog_views import (
    AnimeCatalogSectionView,
    AnimeCatalogYearView,
    AnimeCatalogGenreView,
    AnimeCatalogTypeView,
    AnimeCatalogStatusView,
)

from apps.anime.application.views_clip import ClipTaskViewSet, ScreenshotView
from apps.anime.presentation.views.clip_views import ClipCreateView
from apps.anime.presentation.views.screenshot_views import (
    KodikInstantScreenshotView,
    KodikClipCreateView,
    KodikStreamView,
    DirectVideoUrlView,
)
from apps.anime.presentation.views.anime_api_views import GenresAPI, CatalogTypesAPI
from apps.anime.presentation.views.alternative_stream_views import (
    AlternativeStreamContentView,
    AnimeAlternativeStreamsView,
)

router = DefaultRouter()
router.register(r"admin/franchises", AdminFranchiseViewSet, basename="admin-franchise")
router.register(r"franchises", FranchiseViewSet, basename="franchise")
router.register(r"genres", GenresViewSet, basename="genres")
router.register(r"announcements", AnnouncementViewSet, basename="announcement")
router.register(r"", AnimeViewSet, basename="anime")

router_urls = router.urls

from .views.seo_hub_view import seo_hub_view
from .views.excerpt_views import excerpts, excerpt_detail, excerpt_shared, excerpt_checks

urlpatterns = [
    path('excerpts/check/', excerpt_checks, name='excerpt-checks'),
    path(
        'admin/franchises/rebuild/',
        AdminFranchiseViewSet.as_view({'post': 'rebuild'}),
        name='admin-franchises-rebuild',
    ),
    path(
        'admin/franchises/rebuild-status/<str:rebuild_id>/',
        AdminFranchiseViewSet.as_view({'get': 'rebuild_status'}),
        name='admin-franchises-rebuild-status',
    ),
    path('admin/anime-search/', AdminAnimeSearch.as_view()),
    path('admin/catalog-options/', CatalogOptions.as_view()),
    path('admin/catalog-rules/', CatalogRules.as_view({'get': 'list', 'post': 'create'})),
    path('admin/catalog-rules/apply-all/', CatalogRules.as_view({'post': 'apply_all'})),
    path('admin/catalog-rules/<int:pk>/', CatalogRules.as_view({'post': 'apply', 'delete': 'destroy'})),
    path('admin/catalog-hidden/', CatalogHidden.as_view()),
    path('admin/catalog-hidden/<int:pk>/restore/', CatalogHidden.as_view()),
    path('excerpts/', excerpts),
    path('excerpts/<int:pk>/', excerpt_detail),
    path('excerpts/shared/<uuid:token>/', excerpt_shared),
    path("year/<int:year>/", seo_hub_view, name="seo-year"),
    path("genre/<slug:slug>/", seo_hub_view, name="seo-genre"),
    path("studio/<slug:slug>/", seo_hub_view, name="seo-studio"),
    path("status/<str:status>/", seo_hub_view, name="seo-status"),
    path("search/", SearchAPIView.as_view(), name="anime-search"),
    path("attachment-search/", attachment_anime_search, name="anime-attachment-search"),
    path("parser/status/", ParserStatusAPIView.as_view(), name="parser-status"),
    path("updates/", UpdatesAPIView.as_view(), name="anime-updates"),
    path("home/", HomeAPIView.as_view(), name="anime-home"),
    path(
        "home/personalized/feedback/",
        PersonalizedRecommendationsView.as_view(),
        name="anime-home-personalized-feedback",
    ),
    path(
        "home/personalized/",
        PersonalizedRecommendationsView.as_view(),
        name="anime-home-personalized",
    ),
    path("random/", RandomAnimeView.as_view(), name="anime-random"),
    path(
        "currently-watching/",
        CurrentlyWatchingView.as_view(),
        name="anime-currently-watching",
    ),
    path("active-tab/", UserActiveTabView.as_view(), name="anime-active-tab"),
    path("watch-history/", WatchHistoryView.as_view(), name="watch-history"),
    path(
        "watch-history/<int:anime_id>/",
        WatchHistoryItemView.as_view(),
        name="watch-history-item",
    ),
    path(
        "<int:anime_id>/episode-progress/",
        EpisodeProgressView.as_view(),
        name="episode-progress",
    ),
    path(
        "<int:anime_id>/episode-progress/<int:episode_number>/undo/",
        EpisodeProgressUndoView.as_view(),
        name="episode-progress-undo",
    ),
    path("import-from-kodik/", KodikImportView.as_view(), name="import-from-kodik"),
    path("kodik-filters/", KodikFiltersView.as_view(), name="kodik-filters"),
    path("kodik/search-candidates/", KodikSearchCandidatesView.as_view(), name="kodik-search-candidates"),
    path("kodik/user-add/", KodikUserAddView.as_view(), name="kodik-user-add"),
    path("kodik/user-add/progress/", KodikUserAddView.as_view(), name="kodik-user-add-progress"),
    path("kodik/my-requests/", KodikMyRequestsView.as_view(), name="kodik-my-requests"),
    path(
        "<int:pk>/kodik_translations/",
        KodikTranslationsView.as_view(),
        name="kodik-translations",
    ),
    path(
        "<int:pk>/kodik_player/",
        KodikPlayerView.as_view(),
        name="kodik-player",
    ),
    path(
        "<int:pk>/alternative_streams/",
        AnimeAlternativeStreamsView.as_view(),
        name="anime-alternative-streams",
    ),
    path(
        "alternative-stream/content/",
        AlternativeStreamContentView.as_view(),
        name="anime-alternative-stream-content",
    ),
    path(
        "<int:anime_id>/custom_dubs/",
        CustomDubListView.as_view(),
        name="custom-dubs-list",
    ),
    path(
        "<int:anime_id>/custom_dubs/<int:dub_id>/",
        CustomDubDetailView.as_view(),
        name="custom-dub-detail",
    ),
    path("<int:pk>/themes/", AnimeThemesView.as_view(), name="anime-themes"),
    path(
        "<int:pk>/kodik_video_url/", KodikVideoUrlView.as_view(), name="kodik-video-url"
    ),
    path("<int:pk>/clip/", KodikClipDownloadView.as_view(), name="kodik-clip-download"),
    path(
        "<int:pk>/episode-notifications/",
        AnimeEpisodeNotificationView.as_view(),
        name="anime-episode-notifications",
    ),
    path(
        "admin/today-added/",
        AdminTodayAddedAnimeView.as_view(),
        name="admin-today-added",
    ),
    
    path("catalog-settings/", CatalogSettingsView.as_view(), name="catalog-settings"),
    path("admin/catalog-settings/", CatalogSettingsView.as_view(), name="admin-catalog-settings"),
    path("calendar/", CalendarView.as_view(), name="anime-calendar"),
    path("genres/", GenresAPI.as_view(), name="catalog-genres"),
    path("types/", CatalogTypesAPI.as_view(), name="catalog-types"),
    
    path("clips/", ClipTaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='clip-tasks-list'),
    path("clips/<uuid:pk>/", ClipTaskViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='clip-task-detail'),
    path("clips/<uuid:pk>/status/", ClipTaskViewSet.as_view({'get': 'status'}), name='clip-task-status'),
    path("clips/<uuid:pk>/retry/", ClipTaskViewSet.as_view({'post': 'retry'}), name='clip-task-retry'),
    
    path("screenshot/", ScreenshotView.as_view(), name='screenshot-create'),
    path("clip/create/", ClipCreateView.as_view(), name='clip-create'),
    
    path("<int:pk>/screenshot/", KodikInstantScreenshotView.as_view(), name="anime-instant-screenshot"),
    path("<int:pk>/clip/create/", KodikClipCreateView.as_view(), name="anime-clip-create"),
    path("<int:pk>/stream/", KodikStreamView.as_view(), name="anime-stream"),
    path("<int:pk>/direct_url/", DirectVideoUrlView.as_view(), name="anime-direct-url"),

    path("catalog/<str:section>/", AnimeCatalogSectionView.as_view(), name="anime-catalog-section"),
    path("catalog/year/<int:year>/", AnimeCatalogYearView.as_view(), name="anime-catalog-year"),
    path("catalog/genre/<str:genre>/", AnimeCatalogGenreView.as_view(), name="anime-catalog-genre"),
    path("catalog/type/<str:kind>/", AnimeCatalogTypeView.as_view(), name="anime-catalog-type"),
    path("catalog/status/<str:status>/", AnimeCatalogStatusView.as_view(), name="anime-catalog-status"),
    
    path("", include((router_urls, 'anime'), namespace='anime')),
]
