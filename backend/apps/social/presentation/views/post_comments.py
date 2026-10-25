from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from apps.social.application.post_access import resolve_post_id
from apps.social.application.post_comments import comments_for, create_comment, change_comment
from apps.social.presentation.serializers.social_serializers import PostCommentSerializer


class PostCommentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [AllowAny()] if self.action in ('list', 'retrieve') else [IsAuthenticated()]

    def represent(self, comment):
        return PostCommentSerializer(comment, context={'request': self.request}).data

    def list(self, request, post_pk=None):
        try:
            limit = max(1, min(int(request.query_params.get('page_size', 100)), 200))
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError: raise ValidationError('Некорректная страница')
        queryset = comments_for(request.user, resolve_post_id(post_pk))
        order = ('path', 'pk') if request.query_params.get('sort') == 'tree' else ('-created_at', '-pk')
        rows = queryset.order_by(*order)[(page-1)*limit:page*limit]
        return Response(PostCommentSerializer(rows, many=True, context={'request': request}).data,
                        headers={'X-Total-Count': queryset.count(), 'X-Page-Size': limit})

    def create(self, request, post_pk=None):
        comment, created = create_comment(request, resolve_post_id(post_pk))
        return Response(self.represent(comment), status=201 if created else 200)

    def retrieve(self, request, post_pk=None, pk=None):
        return Response(self.represent(get_object_or_404(comments_for(request.user, resolve_post_id(post_pk)), pk=pk)))

    def update(self, request, post_pk=None, pk=None):
        return Response(self.represent(change_comment(request, resolve_post_id(post_pk), pk)))

    partial_update = update

    def destroy(self, request, post_pk=None, pk=None):
        change_comment(request, resolve_post_id(post_pk), pk, delete=True)
        return Response(status=204)
