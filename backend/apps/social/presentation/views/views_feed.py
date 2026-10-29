from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Count

from apps.social.infrastructure.models.social import Post, Follow, GroupMembership, UserPostHidden
from apps.social.presentation.serializers.social_serializers import FeedPostSerializer, PostSerializer
from apps.social.application.feed_service import FeedGenerationService, TrendingService
import logging



logger = logging.getLogger(__name__)


def cursor_headers(data):
    headers = {'X-Next-Cursor': data['next_cursor'] or ''}
    if data['count'] is not None:
        headers['X-Total-Count'] = str(data['count'])
    return headers


class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.social.application.post_access import readable_posts
        from apps.social.application.post_feed import read_queryset
        base = readable_posts(Post.objects.all(), self.request.user).exclude(post_type='system')
        base = base.exclude(pk__in=UserPostHidden.objects.filter(user=self.request.user).values('post_id'))
        return read_queryset(base.order_by('-created_at', '-pk'), self.request.user)

    def list(self, request, *args, **kwargs):
        from apps.social.application.post_feed import page
        return Response(page(request, 'extended'))

    @action(detail=False, methods=["get"])
    def weighted(self, request):
        from apps.social.application.post_feed import page
        return Response(page(request, 'weighted'))

    @action(detail=False, methods=["get"])
    def hot(self, request):
        from apps.social.application.post_feed import ranked
        data = ranked(request, 'hot')
        if 'page_size' in request.query_params or 'cursor' in request.query_params: return Response(data)
        return Response(data['results'], headers=cursor_headers(data))

    @action(detail=False, methods=["get"])
    def top(self, request):
        from apps.social.application.post_feed import ranked
        data = ranked(request, 'top')
        if 'page_size' in request.query_params or 'cursor' in request.query_params: return Response(data)
        return Response(data['results'], headers=cursor_headers(data))

    @action(detail=False, methods=["get"])
    def trending(self, request):
        from apps.social.application.post_feed import ranked
        data = ranked(request, 'trending')
        if 'page_size' in request.query_params or 'cursor' in request.query_params: return Response(data)
        return Response(data['results'], headers=cursor_headers(data))

    @action(detail=False, methods=["get"])
    def followers(self, request):
        from apps.social.application.post_feed import page
        return Response(page(request, 'followers'))

    @action(detail=False, methods=["get"])
    def matching_channels(self, request):
        limit = int(request.query_params.get("limit", 5))
        return Response({"results": [], "count": 0})
