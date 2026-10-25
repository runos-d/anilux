from rest_framework import viewsets, filters, generics, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q, Avg
from django.db.models import Count
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from apps.dubs.infrastructure.models.dubs import DubGroup, Dub, VoiceActor, Person
from apps.dubs.infrastructure.models.dubs import DubGroupSubscription, DubGroupRating, DubGroupNews, DubGroupDiscussion, DubGroupDiscussionReply
from apps.dubs.presentation.serializers.dubs_serializers import (
    DubGroupSerializer, DubGroupListSerializer, DubSerializer,
    VoiceActorSerializer, AnimeDubSerializer, CreateDubSerializer, UpdateDubSerializer,
    PersonSerializer, PersonDetailSerializer,
    DubGroupRatingSerializer, DubGroupNewsSerializer, DubGroupDiscussionSerializer,
)
from apps.anime.infrastructure.models.anime import Anime

class DubGroupViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = DubGroup.objects.filter(status='active').order_by('name')
    serializer_class = DubGroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']

    @method_decorator(cache_page(60 * 60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 60 * 6))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_value = self.kwargs.get('pk') or self.kwargs.get('slug')
        
        if not lookup_value:
            raise Http404
        
        try:
            obj = queryset.get(slug=lookup_value)
        except DubGroup.DoesNotExist:
            if lookup_value.isdigit():
                try:
                    obj = queryset.get(pk=lookup_value)
                except DubGroup.DoesNotExist:
                    raise Http404
            else:
                raise Http404
        except DubGroup.MultipleObjectsReturned:
            raise Http404
        
        self.check_object_permissions(self.request, obj)
        return obj
    
    @action(detail=True, methods=['get'])
    def dubs(self, request, pk=None):
        group = self.get_object()
        dubs = group.dubs.all().select_related('anime')
        
        page = self.paginate_queryset(dubs)
        if page is not None:
            serializer = DubSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DubSerializer(dubs, many=True)
        return Response(serializer.data)


class DubViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Dub.objects.all().select_related('group', 'anime')
    serializer_class = DubSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['group', 'anime', 'dub_type', 'is_complete']


class VoiceActorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = VoiceActor.objects.all().order_by('name')
    serializer_class = VoiceActorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def anime_dubs(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    if request.method == 'GET':
        dubs = Dub.objects.filter(anime=anime).select_related('group').order_by('-average_rating')
        serializer = AnimeDubSerializer(dubs, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CreateDubSerializer(data=request.data, context={'anime': anime, 'user': request.user})
        if serializer.is_valid():
            dub = serializer.save()
            response_serializer = AnimeDubSerializer(dub)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def dub_detail(request, dub_id):
    dub = get_object_or_404(Dub.objects.select_related('group', 'anime'), id=dub_id)

    if request.method in ['PUT', 'PATCH', 'DELETE']:
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Необходимо авторизоваться для изменения озвучки'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            if not hasattr(dub, 'created_by') or not dub.created_by or dub.created_by != request.user:
                return Response({'error': 'У вас нет прав на изменение этой озвучки'}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Dub ownership check failed", exc_info=True)
            return Response({'error': 'У вас нет прав на изменение этой озвучки'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = AnimeDubSerializer(dub)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = UpdateDubSerializer(dub, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            updated_dub = serializer.save()
            response_serializer = AnimeDubSerializer(updated_dub)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        dub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_dub_groups(request):
    groups = DubGroup.objects.filter(status='active').order_by('-works_count')[:10]
    serializer = DubGroupSerializer(groups, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def anime_dub_groups(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    existing_dubs = Dub.objects.filter(anime=anime).select_related('group').defer('created_by').order_by('-average_rating')

    result = []
    for dub in existing_dubs:
        group_data = DubGroupSerializer(dub.group).data
        group_data['has_dub'] = True
        dub_copy = dub
        dub_data = {
            'id': dub.id,
            'group': {
                'id': dub.group.id,
                'name': dub.group.name,
                'slug': dub.group.slug,
                'logo_url': dub.group.logo_url
            },
            'dub_type': dub.dub_type,
            'dub_type_display': dub.get_dub_type_display(),
            'quality': dub.quality,
            'episodes_done': dub.episodes_done,
            'total_episodes': dub.total_episodes,
            'is_complete': dub.is_complete,
            'average_rating': dub.average_rating,
            'ratings_count': dub.ratings_count,
            'external_url': dub.external_url,
            'created_by': None  
        }
        group_data['dub_info'] = dub_data
        result.append(group_data)

    return Response(result)


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Person.objects.all().order_by('name')
    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'name_jp']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PersonDetailSerializer
        return PersonSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(roles__contains=[role])
        
        return queryset


import os
from django.conf import settings

from apps.anime.infrastructure.api.external_anime_api import external_anime_api


@api_view(['GET'])
def kodik_translation_anime(request, translation_id):
    translation_id = str(translation_id)

    try:
        data = external_anime_api.search(
            translation_id=translation_id,
            types="anime-serial,anime",
            limit=30,
        )

        results = data.get("results", [])

        anime_list = []
        for item in results:
            anime_list.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'title_orig': item.get('title_orig'),
                'year': item.get('year'),
                'type': item.get('type'),
                'quality': item.get('quality'),
                'link': item.get('link'),
                'poster_url': item.get('material_data', {}).get('poster_url') if item.get('material_data') else None,
                'shikimori_id': item.get('shikimori_id'),
                'kinopoisk_id': item.get('kinopoisk_id'),
                'last_season': item.get('last_season'),
                'last_episode': item.get('last_episode'),
                'episodes_count': item.get('episodes_count'),
                'translation': item.get('translation'),
            })

        return Response({
            'count': data.get('total', len(anime_list)),
            'results': anime_list
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)



def _get_group_by_slug_or_id(slug_or_id):
    try:
        return DubGroup.objects.get(slug=slug_or_id)
    except DubGroup.DoesNotExist:
        if slug_or_id.isdigit():
            return DubGroup.objects.get(pk=slug_or_id)
        raise Http404


class DubGroupWorksView(generics.ListAPIView):
    serializer_class = DubSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        qs = group.group_dubs.filter(anime__title_ru__regex=r"[а-яёА-ЯЁ]").select_related('anime')

        dub_type = self.request.query_params.get('dub_type', '')
        if dub_type:
            qs = qs.filter(dub_type=dub_type)

        is_complete = self.request.query_params.get('is_complete', '')
        if is_complete:
            qs = qs.filter(is_complete=is_complete.lower() == 'true')

        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(Q(anime__title_ru__icontains=search) | Q(anime__title_en__icontains=search))

        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-average_rating', 'average_rating', '-anime__year', 'anime__year']
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs


class DubGroupStaffView(generics.ListAPIView):
    serializer_class = VoiceActorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        return group.voice_actors.all()


class DubGroupNewsView(generics.ListAPIView):
    serializer_class = DubGroupNewsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        return group.news.all()


class DubGroupDiscussionsView(generics.ListAPIView):
    serializer_class = DubGroupDiscussionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-likes_count', '-replies_count']
        qs = group.discussions.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class DubGroupDiscussionCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title or not content:
            return Response({'error': 'Заголовок и содержание обязательны'}, status=400)
        disc = DubGroupDiscussion.objects.create(
            group=group,
            author=request.user,
            title=title,
            content=content,
        )
        return Response(DubGroupDiscussionSerializer(disc).data, status=201)


class DubGroupReviewsView(generics.ListAPIView):
    serializer_class = DubGroupRatingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-overall_rating', 'overall_rating']
        qs = group.ratings.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class DubGroupReviewCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        data = request.data
        rating, _ = DubGroupRating.objects.update_or_create(
            user=request.user,
            group=group,
            defaults={
                'voice_quality': int(data.get('voice_quality', 5)),
                'timing': int(data.get('timing', 5)),
                'translation': int(data.get('translation', 5)),
                'consistency': int(data.get('consistency', 5)),
                'comment': data.get('comment', ''),
            }
        )
        reviews_count = group.ratings.count()
        if reviews_count <= 1:
            initial = group.average_rating if group.average_rating else rating.overall_rating
            n = 10
            new_avg = (initial * n + rating.overall_rating) / (n + 1)
        else:
            avg = group.ratings.aggregate(avg=Avg('overall_rating'))['avg'] or 0
            new_avg = avg
        DubGroup.objects.filter(pk=group.pk).update(average_rating=round(new_avg, 2))
        return Response(DubGroupRatingSerializer(rating).data, status=201)


class DubGroupSubscribeView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        sub, created = DubGroupSubscription.objects.get_or_create(user=request.user, group=group)
        if created:
            DubGroup.objects.filter(pk=group.pk).update(subscribers_count=group.subscriptions.count())
        return Response({'subscribed': True, 'subscribers_count': group.subscriptions.count()})

    def delete(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        DubGroupSubscription.objects.filter(user=request.user, group=group).delete()
        DubGroup.objects.filter(pk=group.pk).update(subscribers_count=group.subscriptions.count())
        return Response({'subscribed': False, 'subscribers_count': group.subscriptions.count()})


class DubGroupSimilarView(generics.ListAPIView):
    serializer_class = DubGroupListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])

        my_genres = set((group.genre_stats or {}).keys())

        candidates = DubGroup.objects.filter(
            status='active'
        ).exclude(pk=group.pk)

        scored = []
        for g in candidates:
            score = 0
            if g.translation_type == group.translation_type:
                score += 3
            other_genres = set((g.genre_stats or {}).keys())
            if my_genres and other_genres:
                intersection = my_genres & other_genres
                union = my_genres | other_genres
                jaccard = len(intersection) / len(union) if union else 0
                score += jaccard * 5
            if group.average_rating and g.average_rating:
                rating_diff = abs(group.average_rating - g.average_rating)
                if rating_diff < 1.0:
                    score += 1
            scored.append((score, g))

        scored.sort(key=lambda x: (-x[0], -x[1].average_rating))
        return [s for _, s in scored[:8]]


class DubGroupDiscussionRepliesView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        replies = disc.replies.all().select_related('author')
        data = []
        for r in replies:
            avatar = None
            if hasattr(r.author, 'avatar') and r.author.avatar:
                avatar = r.author.avatar.url
            data.append({
                'id': r.id,
                'author_name': r.author.username,
                'author_avatar': avatar,
                'content': r.content,
                'created_at': r.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Содержание обязательно'}, status=400)
        reply = DubGroupDiscussionReply.objects.create(
            discussion=disc,
            author=request.user,
            content=content,
        )
        from django.utils import timezone
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(
            replies_count=disc.replies.count(),
            last_reply_at=timezone.now()
        )
        avatar = None
        if hasattr(reply.author, 'avatar') and reply.author.avatar:
            avatar = reply.author.avatar.url
        return Response({
            'id': reply.id,
            'author_name': reply.author.username,
            'author_avatar': avatar,
            'content': reply.content,
            'created_at': reply.created_at.isoformat(),
        }, status=201)


def _dub_group_safe_increment(val):
    return (val or 0) + 1


class DubGroupDiscussionLikeView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        disc.likes_count = _dub_group_safe_increment(disc.likes_count)
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(likes_count=disc.likes_count)
        return Response({'likes_count': disc.likes_count})


class DubGroupDiscussionDislikeView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        disc.dislikes_count = _dub_group_safe_increment(disc.dislikes_count)
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(dislikes_count=disc.dislikes_count)
        return Response({'dislikes_count': disc.dislikes_count})


@api_view(['GET'])
def kodik_translation_detail(request, translation_id):
    translation_id = str(translation_id)

    try:
        translations_data = external_anime_api.get_translations_v1(
            types="anime-serial,anime",
        )
        translations = translations_data.get("results", [])

        translation = None
        for t in translations:
            if str(t.get('id')) == translation_id:
                translation = t
                break

        if not translation:
            return Response({'error': 'Translation not found'}, status=404)

        anime_data = external_anime_api.search(
            translation_id=translation_id,
            types="anime-serial,anime",
            limit=30,
        )

        return Response({
            'id': translation.get('id'),
            'title': translation.get('title'),
            'type': translation.get('type'),
            'anime_count': anime_data.get('total', 0),
            'anime': anime_data.get('results', [])[:10],
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)
