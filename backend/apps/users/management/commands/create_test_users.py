from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.users.infrastructure.models.users import User, UserSettings


class Command(BaseCommand):
    help = 'Create 10 test users with settings'

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'testuser1',
                'email': 'test1@example.com',
                'password': 'testpass123',
                'first_name': 'Алексей',
                'last_name': 'Смирнов',
                'display_name': 'Алексей Смирнов',
                'nickname': 'alex_s',
                'bio': 'Люблю аниме и код',
                'level': 5,
            },
            {
                'username': 'testuser2',
                'email': 'test2@example.com',
                'password': 'testpass123',
                'first_name': 'Мария',
                'last_name': 'Кузнецова',
                'display_name': 'Мария К.',
                'nickname': 'maria_k',
                'bio': 'Фанат студии Ghibli',
                'level': 12,
            },
            {
                'username': 'testuser3',
                'email': 'test3@example.com',
                'password': 'testpass123',
                'first_name': 'Дмитрий',
                'last_name': 'Попов',
                'display_name': 'Дмитрий Попов',
                'nickname': 'dima_p',
                'bio': 'Смотрю всё подряд',
                'level': 3,
            },
            {
                'username': 'testuser4',
                'email': 'test4@example.com',
                'password': 'testpass123',
                'first_name': 'Анна',
                'last_name': 'Васильева',
                'display_name': 'Анна В.',
                'nickname': 'anna_v',
                'bio': 'Онлайн почти всегда',
                'level': 8,
            },
            {
                'username': 'testuser5',
                'email': 'test5@example.com',
                'password': 'testpass123',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'display_name': 'Иван Петров',
                'nickname': 'ivan_p',
                'bio': 'Коллекционирую тайтлы',
                'level': 15,
            },
            {
                'username': 'testuser6',
                'email': 'test6@example.com',
                'password': 'testpass123',
                'first_name': 'Елена',
                'last_name': 'Соколова',
                'display_name': 'Елена Соколова',
                'nickname': 'elena_s',
                'bio': 'Обожаю саундтреки',
                'level': 7,
            },
            {
                'username': 'testuser7',
                'email': 'test7@example.com',
                'password': 'testpass123',
                'first_name': 'Артём',
                'last_name': 'Михайлов',
                'display_name': 'Артём М.',
                'nickname': 'artem_m',
                'bio': 'Рисуем по аниме',
                'level': 20,
            },
            {
                'username': 'testuser8',
                'email': 'test8@example.com',
                'password': 'testpass123',
                'first_name': 'Ольга',
                'last_name': 'Новикова',
                'display_name': 'Ольга Н.',
                'nickname': 'olga_n',
                'bio': 'Пишу рецензии',
                'level': 10,
            },
            {
                'username': 'testuser9',
                'email': 'test9@example.com',
                'password': 'testpass123',
                'first_name': 'Сергей',
                'last_name': 'Федоров',
                'display_name': 'Сергей Федоров',
                'nickname': 'sergey_f',
                'bio': 'Старый фанат аниме',
                'level': 25,
            },
            {
                'username': 'testuser10',
                'email': 'test10@example.com',
                'password': 'testpass123',
                'first_name': 'Наталья',
                'last_name': 'Морозова',
                'display_name': 'Наталья Морозова',
                'nickname': 'nataly_m',
                'bio': 'Изучаю японский',
                'level': 6,
            },
        ]

        created_count = 0
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'password': make_password(data['password']),
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'display_name': data['display_name'],
                    'nickname': data['nickname'],
                    'bio': data['bio'],
                    'level': data['level'],
                }
            )

            if created:
                UserSettings.objects.get_or_create(user=user)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {user.username} ({user.display_name})'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone. Created {created_count} users.'))
