from rest_framework import serializers
from apps.dubs.infrastructure.models.dubs import DubGroup, Dub, VoiceActor, DubRole, DubLink, Person
from apps.dubs.infrastructure.models.dubs import DubGroupSubscription, DubGroupRating, DubGroupNews, DubGroupDiscussion, DubGroupDiscussionReply


class DubGroupListSerializer(serializers.ModelSerializer):
    logo_image_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    def get_logo_image_url(self, obj):
        return obj.logo_image_url

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return DubGroupSubscription.objects.filter(user=request.user, group=obj).exists()
        return False

    class Meta:
        model = DubGroup
        fields = [
            'id', 'name', 'name_jp', 'slug', 'translation_type',
            'works_count', 'average_rating', 'subscribers_count',
            'logo_image_url', 'is_subscribed', 'is_verified',
        ]


class DubGroupSerializer(serializers.ModelSerializer):
    logo_image_url = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    top_anime = serializers.SerializerMethodField()

    def get_logo_image_url(self, obj):
        return obj.logo_image_url

    def get_banner_image_url(self, obj):
        return obj.banner_image_url

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return DubGroupSubscription.objects.filter(user=request.user, group=obj).exists()
        return False

    def get_rating_distribution(self, obj):
        from django.db.models import Count
        ratings = obj.ratings.values('overall_rating').annotate(count=Count('id'))
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = obj.ratings.count()
        for r in ratings:
            key = round(r['overall_rating'])
            if key in dist:
                dist[key] += r['count']
        if total > 0:
            return {k: round(v / total * 100) for k, v in dist.items()}
        return dist

    def get_top_anime(self, obj):
        top_dubs = obj.group_dubs.filter(
            anime__isnull=False,
            average_rating__isnull=False
        ).select_related('anime').order_by('-average_rating')[:5]
        
        result = []
        for dub in top_dubs:
            if dub.anime:
                result.append({
                    'id': dub.anime.id,
                    'anime_url': f'/anime/{dub.anime.id}',
                    'anime_title': dub.anime.title_ru or dub.anime.title_en,
                    'anime_score': dub.average_rating,
                    'anime_poster': dub.anime.poster_image_url if dub.anime.poster else dub.anime.poster_url,
                    'anime_kind': dub.anime.kind,
                })
        return result

    class Meta:
        model = DubGroup
        fields = [
            'id', 'name', 'name_jp', 'slug', 'description',
            'website', 'vk_url', 'telegram_url', 'discord_url', 'youtube_url', 'twitter_url',
            'founded_year', 'translation_type',
            'works_count', 'tv_count', 'movie_count', 'ova_count',
            'average_rating', 'subscribers_count',
            'genre_stats',
            'logo_image_url', 'banner_image_url',
            'is_subscribed', 'is_verified',
            'rating_distribution', 'top_anime',
            'created_at',
        ]
    

class DubGroupRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.username

    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            return obj.user.avatar.url
        return None

    class Meta:
        model = DubGroupRating
        fields = [
            'id', 'user_name', 'user_avatar',
            'voice_quality', 'timing', 'translation', 'consistency',
            'overall_rating', 'comment', 'created_at',
        ]


class DubGroupNewsSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    def get_author_name(self, obj):
        return obj.author.username if obj.author else 'Редакция'

    class Meta:
        model = DubGroupNews
        fields = ['id', 'title', 'content', 'author_name', 'likes_count', 'comments_count', 'created_at']


class DubGroupDiscussionSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()

    def get_author_name(self, obj):
        return obj.author.username

    def get_author_avatar(self, obj):
        if hasattr(obj.author, 'avatar') and obj.author.avatar:
            return obj.author.avatar.url
        return None

    class Meta:
        model = DubGroupDiscussion
        fields = [
            'id', 'title', 'content', 'author_name', 'author_avatar',
            'likes_count', 'dislikes_count', 'replies_count',
            'is_pinned', 'created_at', 'last_reply_at',
        ]


class VoiceActorSerializer(serializers.ModelSerializer):
    groups = DubGroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = VoiceActor
        fields = [
            'id', 'name', 'slug', 'description',
            'photo_url', 'groups', 'roles_count',
            'created_at'
        ]


class DubLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DubLink
        fields = ['id', 'source', 'url', 'episode', 'quality', 'is_active']


class DubRoleSerializer(serializers.ModelSerializer):
    actor = VoiceActorSerializer(read_only=True)
    
    class Meta:
        model = DubRole
        fields = ['id', 'actor', 'character_name', 'character_name_en', 'is_main']


class DubSerializer(serializers.ModelSerializer):
    group = DubGroupSerializer(read_only=True)
    roles = DubRoleSerializer(many=True, read_only=True)
    links = DubLinkSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dub
        fields = [
            'id', 'group', 'dub_type', 'quality',
            'episodes_done', 'total_episodes', 'is_complete', 'is_abandoned',
            'external_url', 'average_rating', 'ratings_count',
            'started_at', 'finished_at', 'last_episode_at',
            'roles', 'links', 'created_at'
        ]


class AnimeDubSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField()
    dub_type_display = serializers.CharField(source='get_dub_type_display', read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Dub
        fields = [
            'id', 'group', 'dub_type', 'dub_type_display', 'quality',
            'episodes_done', 'total_episodes', 'is_complete',
            'average_rating', 'ratings_count', 'external_url', 'created_by'
        ]

    def get_group(self, obj):
        return {
            'id': obj.group.id,
            'name': obj.group.name,
            'slug': obj.group.slug,
            'logo_url': obj.group.logo_url
        }

    def get_created_by(self, obj):
        try:
            if hasattr(obj, 'created_by') and obj.created_by:
                return {
                    'id': obj.created_by.id,
                    'username': obj.created_by.username
                }
        except Exception:
            pass
        return None


class UpdateDubSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(write_only=True, max_length=200, required=False)
    group_links = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Dub
        fields = [
            'group_name', 'group_links',
            'dub_type', 'external_url', 'episodes_done', 'total_episodes'
        ]

    def update(self, instance, validated_data):
        group_name = validated_data.pop('group_name', None)
        group_links = validated_data.pop('group_links', [])

        if group_name and group_name != instance.group.name:
            from apps.dubs.infrastructure.models.dubs import DubGroup

            links_data = {}
            link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
            for i, url in enumerate(group_links[:4]):
                if url.strip():
                    links_data[link_fields[i]] = url.strip()

            group, created = DubGroup.objects.get_or_create(
                name__iexact=group_name,
                defaults={
                    'name': group_name,
                    'status': 'active',
                    **links_data
                }
            )

            if not created:
                for key, value in links_data.items():
                    if value:
                        setattr(group, key, value)
                group.save()

            if Dub.objects.filter(anime=instance.anime, group=group).exclude(id=instance.id).exists():
                raise serializers.ValidationError("Озвучка этой группы для данного аниме уже существует.")

            instance.group = group
        elif group_links:
            links_data = {}
            link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
            for i, url in enumerate(group_links[:4]):
                if url.strip():
                    links_data[link_fields[i]] = url.strip()

            for key, value in links_data.items():
                if value:
                    setattr(instance.group, key, value)
            instance.group.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CreateDubSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(write_only=True, max_length=200)
    group_links = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Dub
        fields = [
            'group_name', 'group_links',
            'dub_type', 'external_url', 'episodes_done', 'total_episodes'
        ]

    def validate_group_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Название группы озвучки обязательно.")
        return value.strip()

    def validate_group_links(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Ссылки должны быть списком.")

        for url in value:
            if not url.strip():
                raise serializers.ValidationError("URL ссылки не может быть пустым.")

        return value

    def create(self, validated_data):
        anime = self.context['anime']
        group_name = validated_data.pop('group_name')
        group_links = validated_data.pop('group_links', [])

        from apps.dubs.infrastructure.models.dubs import DubGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = self.context.get('user')
        if user and not user.is_authenticated:
            user = None

        links_data = {}
        link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
        for i, url in enumerate(group_links[:4]):  
            if url.strip():
                links_data[link_fields[i]] = url.strip()

        group, created = DubGroup.objects.get_or_create(
            name__iexact=group_name,
            defaults={
                'name': group_name,
                'status': 'active',
                **links_data
            }
        )

        if not created:
            for key, value in links_data.items():
                if value:
                    setattr(group, key, value)
            group.save()

        if Dub.objects.filter(anime=anime, group=group).exists():
            raise serializers.ValidationError("Озвучка этой группы для данного аниме уже существует.")

        dub_data = {'anime': anime, 'group': group, **validated_data}
        if user and user.is_authenticated:
            dub_data['created_by'] = user
        dub = Dub.objects.create(**dub_data)
        return dub


class PersonSerializer(serializers.ModelSerializer):
    roles_display = serializers.SerializerMethodField()
    anime_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Person
        fields = [
            'id', 'name', 'name_jp', 'slug', 'description',
            'photo_url', 'birth_date', 'roles', 'roles_display',
            'works_count', 'anime_count', 'created_at'
        ]
    
    def get_roles_display(self, obj):
        return [dict(Person.ROLE_CHOICES).get(r, r) for r in obj.roles]
    
    def get_anime_count(self, obj):
        return obj.works_count


class PersonDetailSerializer(PersonSerializer):
    related_anime = serializers.SerializerMethodField()
    
    class Meta(PersonSerializer.Meta):
        fields = PersonSerializer.Meta.fields + ['related_anime']
    
    def get_related_anime(self, obj):
        from apps.anime.presentation.serializers.anime_serializers import AnimeSerializer
        anime_list = obj.related_anime.all()[:10]
        return AnimeSerializer(anime_list, many=True).data