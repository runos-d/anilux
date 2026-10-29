import json
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Seed synthetic catalogue/feed only into the disposable scalability lab'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=120)
        parser.add_argument('--anime', type=int, default=3000)
        parser.add_argument('--posts', type=int, default=10000)

    def handle(self, **options):
        config = connection.settings_dict
        if connection.vendor != 'mysql' or config['HOST'] != 'lab-mysql' or config['NAME'] != 'scalability_lab':
            raise CommandError('Only lab-mysql/scalability_lab can be seeded')
        return self.seed(options)

    @transaction.atomic
    def seed(self, options):
        with connection.cursor() as cursor:
            cursor.execute('SELECT DATABASE()')
            if cursor.fetchone()[0] != 'scalability_lab':
                raise CommandError('Actual database is not the disposable schema')
        users, anime, posts = (options[key] for key in ('users', 'anime', 'posts'))
        if not (1 <= users <= 10000 and 1 <= anime <= 100000 and 0 <= posts <= 1000000):
            raise CommandError('Fixture outside bounded lab size')
        from apps.users.infrastructure.models.users import User
        from apps.anime.models import Anime
        from apps.social.infrastructure.models.social import Post
        if User.objects.exists() or Anime.objects.exists() or Post.objects.exists():
            raise CommandError('Refusing to seed a nonempty schema; existing data is preserved')
        User.objects.bulk_create([User(username=f'load-user-{i}', email=f'load-{i}@example.test', password='!')
                                  for i in range(users)], batch_size=500)
        user_ids = list(User.objects.order_by('pk').values_list('pk', flat=True))
        for offset in range(0, anime, 500):
            Anime.objects.bulk_create([Anime(title_ru=f'Нагрузочный тайтл {i}', slug=f'capacity-anime-{i}',
                shikimori_id=500000+i, is_available=True, has_cyrillic=True, year=2024, score=8, episodes=12)
                for i in range(offset, min(anime, offset+500))])
        for offset in range(0, posts, 500):
            Post.objects.bulk_create([Post(author_id=user_ids[i % users], text=f'Capacity post {i}: ' + 'test ' * 30,
                status='published', visibility='public') for i in range(offset, min(posts, offset+500))])
        self.stdout.write(json.dumps({'users': users, 'anime': anime, 'posts': posts, 'synthetic_only': True}))
