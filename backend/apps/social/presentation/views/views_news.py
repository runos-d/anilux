from django.db.models import F
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.social.infrastructure.models.social_news import News
from apps.social.presentation.serializers.social_serializers import NewsSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated
            and (getattr(user, "is_admin", False) or user.is_staff or user.is_superuser)
        )


class NewsListView(generics.ListCreateAPIView):
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = News.objects.select_related("author").order_by("-is_pinned", "-created_at")
        if not (self.request.user.is_authenticated and (
            getattr(self.request.user, "is_admin", False)
            or self.request.user.is_staff
        )):
            qs = qs.filter(is_published=True)
        return qs


class NewsDetailView(generics.RetrieveAPIView):
    queryset = News.objects.select_related("author")
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        return queryset if user.is_authenticated and user.is_staff else queryset.filter(is_published=True)


class NewsCreateView(generics.CreateAPIView):
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


class NewsUpdateView(generics.UpdateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


class NewsDeleteView(generics.DestroyAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_news_view(request, pk):
    News.objects.filter(pk=pk).update(views_count=F("views_count") + 1)
    views_count = News.objects.filter(pk=pk).values_list("views_count", flat=True).first() or 0
    return Response({"views_count": views_count})
