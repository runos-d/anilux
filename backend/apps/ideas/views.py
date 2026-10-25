from django.db import transaction
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Idea, IdeaVote
from .serializers import IdeaAdminSerializer, IdeaSerializer


class IdeasPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100


class IdeaViewSet(viewsets.ModelViewSet):
    serializer_class = IdeaSerializer
    pagination_class = IdeasPagination
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    search_fields = ["title", "description", "author__username", "author__nickname"]
    ordering_fields = ["created_at", "updated_at", "votes_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Idea.objects.select_related("author")
        status_value = self.request.query_params.get("status")
        kind = self.request.query_params.get("kind")
        mine = self.request.query_params.get("mine")
        search = self.request.query_params.get("search", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)
        if kind:
            queryset = queryset.filter(kind=kind)
        if mine == "1" and self.request.user.is_authenticated:
            queryset = queryset.filter(author=self.request.user)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(author__username__icontains=search)
                | Q(author__nickname__icontains=search)
            )
        return queryset

    def get_serializer_class(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return IdeaAdminSerializer
        return IdeaSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated and self.action == "list":
            context["voted_ids"] = set(
                IdeaVote.objects.filter(user=user).values_list("idea_id", flat=True)
            )
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status=Idea.Status.PENDING)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_staff = request.user.is_staff
        is_owner_edit = instance.author_id == request.user.id and instance.status == Idea.Status.PENDING
        if not is_staff and not is_owner_edit:
            return Response(
                {"detail": "Редактировать запись может её автор до модерации или администратор."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not is_staff:
            allowed = {"title", "description", "kind"}
            if any(key not in allowed for key in request.data):
                return Response(
                    {"detail": "Статус и приоритет меняет администратор."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_staff and not (
            instance.author_id == request.user.id and instance.status == Idea.Status.PENDING
        ):
            return Response(
                {"detail": "Удалить запись может её автор до модерации или администратор."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        idea = self.get_object()
        with transaction.atomic():
            locked_idea = Idea.objects.select_for_update().get(pk=idea.pk)
            vote = IdeaVote.objects.filter(idea=locked_idea, user=request.user).first()
            if vote:
                vote.delete()
                locked_idea.votes_count = max(0, locked_idea.votes_count - 1)
                is_voted = False
            else:
                IdeaVote.objects.create(idea=locked_idea, user=request.user)
                locked_idea.votes_count += 1
                is_voted = True
            locked_idea.save(update_fields=["votes_count"])
        return Response({"is_voted": is_voted, "votes_count": locked_idea.votes_count})
