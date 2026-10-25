from rest_framework import serializers
from apps.notifications.infrastructure.models.notifications import EpisodeSubscription

class EpisodeSubscriptionSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    poster_url = serializers.CharField(source='anime.poster_url', read_only=True)
    from apps.anime.models import Anime
    anime_id = serializers.PrimaryKeyRelatedField(source='anime', queryset=Anime.objects.filter(is_available=True), required=False, write_only=True)
    class Meta:
        model = EpisodeSubscription
        fields = ['id','user','anime','anime_id','anime_title','poster_url','is_active','is_paused','paused_until','last_notified_episode','created_at','updated_at']
        read_only_fields = ['user','created_at','updated_at','last_notified_episode']
        extra_kwargs = {'anime': {'required': False}}

    def validate(self, attrs):
        if not self.instance and not attrs.get('anime'):
            raise serializers.ValidationError({'anime_id': 'Укажите аниме'})
        if attrs.get('anime') and not attrs['anime'].is_available:
            raise serializers.ValidationError({'anime_id': 'Аниме недоступно'})
        if self.instance and 'anime' in attrs and attrs['anime'] != self.instance.anime:
            raise serializers.ValidationError('Нельзя перенести подписку на другое аниме')
        return attrs
