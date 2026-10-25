from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from typing import Dict, Any


class _CatalogAliasHelper:
    permission_classes = [permissions.AllowAny]

    def _run(self, request, **overrides):
        from apps.anime.presentation.views.anime_views import AnimeViewSet
        mutable_get = request._request.GET.copy()
        for key, value in overrides.items():
            if value is None:
                mutable_get.pop(key, None)
            else:
                mutable_get[key] = str(value)
        original_get = request._request.GET
        request._request.GET = mutable_get
        try:
            return AnimeViewSet().list(request)
        finally:
            request._request.GET = original_get


class AnimeCatalogSectionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, section):
        if section == "calendar":
            from apps.anime.presentation.views.anime_views import CalendarView
            return CalendarView.as_view()(request)
        valid_sections = {"ongoings", "announcements", "watching"}
        if section not in valid_sections:
            raise Http404()
        overrides: Dict[str, Any] = {}
        if section == "ongoings":
            overrides["status"] = "ongoing"
        elif section == "announcements":
            overrides["status"] = "announced"
        elif section == "watching":
            overrides["status"] = "ongoing"
            overrides["ordering"] = "-score"
        return _CatalogAliasHelper()._run(request, **overrides)


class AnimeCatalogYearView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, year):
        return _CatalogAliasHelper()._run(request, year_from=str(year), year_to=str(year))


class AnimeCatalogGenreView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, genre):
        return _CatalogAliasHelper()._run(request, genres=genre, genre_logic="OR")


class AnimeCatalogTypeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, kind):
        return _CatalogAliasHelper()._run(request, type=kind)


class AnimeCatalogStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, status):
        return _CatalogAliasHelper()._run(request, status=status)
