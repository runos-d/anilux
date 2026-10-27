import json
import re
from datetime import date
from unittest.mock import patch
from xml.etree import ElementTree

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.http import QueryDict
from django.core.exceptions import ValidationError

from apps.anime.infrastructure.models.anime import Anime, Genre, Franchise, CatalogVisibility, CatalogHideRule
from apps.social.infrastructure.models.social import Post, Group
from apps.playlists.infrastructure.models.playlists import Playlist, PlaylistItem
from .models import SEO_PATH_MAX_LENGTH, SiteSeoSettings, SeoAlias, SeoCollection, SeoOverride, SeoHub
from .service import anime_path, franchise_path, build_page, clean_text
from .navigation import site_navigation
from .tasks import refresh_hubs


@override_settings(
    SEO_PUBLIC_ORIGIN='https://catalog.example.org',
    SEO_INDEXING_ENABLED=True,
    ALLOWED_HOSTS=['testserver', 'catalog.example.org', 'www.catalog.example.org'],
)
class SeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='public-reader', nickname='reader',
            bio='Пишу об аниме, сравниваю экранизации с первоисточниками и собираю тематические подборки для просмотра.')
        cls.franchise = Franchise.objects.create(name='Публичная франшиза', slug='public-franchise')
        cls.romance = Genre.objects.create(name='Романтика', slug='romance')
        cls.small = Genre.objects.create(name='Редкий', slug='small')
        Anime.objects.bulk_create([Anime(title_ru=f'Тестовое аниме {i}', slug=f'anime-{i}', has_cyrillic=True,
            description=f'Описание истории {i}.', year=2025, kind='tv', status='finished', episodes=12,
            genres=['Романтика'] + (['Редкий'] if i < 4 else []), release_date=date(2025, 1, 10),
            franchise=cls.franchise, franchise_order=i) for i in range(30)])
        cls.anime = Anime.objects.order_by('pk').first()
        cls.post = Post.objects.create(author=cls.user, title='Публичный пост', text=(
            'Разбираю, как история раскрывает героев и почему спокойные сцены здесь работают не хуже кульминации. '
            'Без пересказа сюжета: только впечатления от режиссуры, музыки, темпа и развития отношений между персонажами.'))
        cls.playlist = Playlist.objects.create(user=cls.user, title='Публичный список', description=(
            'Подборка законченных историй для спокойного просмотра: без случайных продолжений и незакрытых сюжетных линий.'))
        PlaylistItem.objects.bulk_create([
            PlaylistItem(playlist=cls.playlist, anime=anime, position=index)
            for index, anime in enumerate(Anime.objects.order_by('pk')[:5], 1)
        ])
        cls.collection = SeoCollection.objects.create(slug='romance-2025', name='Романтические аниме 2025 года', filters={'year': 2025, 'genre': 'romance'})

    def get(self, path, **kwargs):
        return self.client.get(path, secure=True, HTTP_HOST='catalog.example.org', **kwargs)

    def payload(self, path):
        return self.get('/api/seo/page/', data={'path': path}).json()

    def test_indexed_seo_paths_are_mysql_safe_and_long_slugs_have_stable_fallbacks(self):
        self.anime.slug = 'a' * 255
        self.assertEqual(len(anime_path(self.anime)), SEO_PATH_MAX_LENGTH)
        self.assertTrue(anime_path(self.anime).startswith(f'/anime/{self.anime.pk}-'))

        self.franchise.slug = 'f' * 255
        self.franchise.save(update_fields=['slug'])
        self.assertEqual(franchise_path(self.franchise), f'/franchise/{self.franchise.pk}')

        self.franchise.slug = 'short-franchise'
        self.franchise.save(update_fields=['slug'])
        self.assertFalse(SeoAlias.objects.filter(path__startswith='/franchise/' + ('f' * 200)).exists())

    def test_global_footer_is_static_on_every_route_and_without_javascript(self):
        navigation = site_navigation()
        self.assertTrue(navigation['groups'], 'The shared frontend navigation registry must be deployed')
        footers = []
        for path in ['/', '/anime', '/@reader', f'/post/{self.post.public_id}', '/login', '/terms', '/not/a/page']:
            html = self.get(path).content.decode()
            footers.append(re.search(r'<footer class="seo-navigation".*?</footer>', html, re.S)[0])
            self.assertEqual(html.count('<footer'), 1)
        self.assertEqual(len(set(footers)), 1)
        self.assertIn('mailto:' + navigation['email'], footers[0])
        self.assertIn('/sakura.svg', footers[0])
        self.assertNotIn('/post/', footers[0])
        self.assertNotIn('/@reader', footers[0])
        for group in navigation['groups']:
            for link in group['links']:
                with self.subTest(path=link['path']):
                    self.assertEqual(self.get(link['path']).status_code, 200)

    def test_legal_pages_follow_the_document_publication_state(self):
        for document in site_navigation()['documents']:
            data = self.payload(document['path'])
            self.assertEqual(data['status'], 200)
            self.assertEqual(data['h1'], document['name'])
            self.assertIn(document['text'], data['contentHtml'])
            expected = 'index,follow' if document.get('published') else 'noindex,follow'
            self.assertEqual(data['robots'], expected)
        self.assertEqual(self.payload('/contacts')['robots'], 'index,follow')

    def test_static_sitemap_does_not_depend_on_hub_refresh(self):
        xml = self.get('/sitemap-pages-1.xml').content.decode()
        for path in ['/', '/anime', '/anime/browse', '/anime/franchises', '/contacts', '/ideas']:
            self.assertIn('<loc>https://catalog.example.org' + path + '</loc>', xml)
        for document in site_navigation()['documents']:
            assertion = self.assertIn if document.get('published') else self.assertNotIn
            assertion(document['path'], xml)
        self.assertIn('sitemap-pages-1.xml', self.get('/sitemap.xml').content.decode())
        SeoOverride.objects.create(path='/contacts', noindex=True)
        self.assertNotIn('/contacts', self.get('/sitemap-pages-1.xml').content.decode())

    def test_ideas_page_has_public_metadata(self):
        data = self.payload('/ideas')
        self.assertEqual(data['status'], 200)
        self.assertIn('Идеи и предложения', data['title'])
        self.assertEqual(data['robots'], 'index,follow')

    def test_roulette_page_has_utility_metadata(self):
        data = self.payload('/roulette')
        self.assertEqual(data['status'], 200)
        self.assertIn('Рулетка аниме', data['title'])
        self.assertIn('настраиваемыми шансами', data['description'])
        self.assertEqual(data['robots'], 'noindex,follow')

    def test_playlist_aliases_match_client_navigation(self):
        for path, target in [('/public-playlists', '/playlists?tab=public'), ('/my-playlists', '/playlists')]:
            response = self.get(path)
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'], 'https://catalog.example.org' + target)
        self.assertIn('Публичные плейлисты', self.payload('/playlists?tab=public')['title'])
        self.assertIn('Мои плейлисты', self.payload('/playlists?tab=my')['title'])

    def test_watch_intent_and_announcements_have_appropriate_metadata(self):
        Anime.objects.filter(pk=self.anime.pk).update(title_ru='Наруто')
        data = self.payload(anime_path(self.anime))
        self.assertIn('Наруто — смотреть аниме онлайн', data['title'])
        self.assertIn('«Наруто» — смотреть онлайн.', data['description'])
        Anime.objects.filter(pk=self.anime.pk).update(status='announced')
        data = self.payload(anime_path(self.anime))
        self.assertIn('дата выхода', data['title'])
        self.assertNotIn('смотреть онлайн', data['title'])
        self.assertNotIn('смотреть онлайн', data['description'].lower())

    def test_metadata_text_has_no_markup_scripts_or_invisible_controls(self):
        self.assertEqual(clean_text('&lt;script&gt;alert(1)&lt;/script&gt; Наруто\u202e\x00  онлайн'), 'Наруто онлайн')
        self.assertEqual(clean_text('x' * 30, 10), 'x' * 9 + '…')
        for path, name in [('/library', 'Моя библиотека'), ('/feed', 'Лента сообщества'), ('/settings', 'Настройки')]:
            self.assertIn(name, self.payload(path)['title'])
            self.assertEqual(self.payload(path)['robots'], 'noindex,follow')

    @override_settings(SEO_SITE_NAME='Каталог аниме')
    def test_catalog_title_does_not_repeat_default_site_name(self):
        self.assertEqual(self.payload('/anime')['title'], 'Каталог аниме')

    def test_document_matrix_and_identical_user_agents(self):
        paths = ['/', '/anime', '/anime/franchises', anime_path(self.anime), '/franchise/public-franchise', '/anime/year/2025',
                 '/anime/genre/romance', '/anime/season/2025/winter', '/anime/type/tv', '/anime/status/finished',
                 '/anime/collection/romance-2025', '/anime/year/2025?page=2', '/@reader',
                 f'/post/{self.post.public_id}', f'/playlist/{self.playlist.pk}']
        for path in paths:
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['X-Robots-Tag'], 'index,follow')
                html = response.content.decode()
                self.assertIn('<h1>', html)
                self.assertIn('index,follow', html)
                self.assertEqual(html.count('rel="canonical"'), 1)
                self.assertEqual(html.count('name="description"'), 1)
                self.assertEqual(html.count('name="robots"'), 1)
                nonces = set(re.findall(r'<script[^>]+nonce="([^"]+)"', html))
                self.assertEqual(len(nonces), 1)
                self.assertIn("'nonce-" + next(iter(nonces)) + "'", response['Content-Security-Policy'])
                for ua in ['Googlebot', 'YandexBot']:
                    bot_html = self.get(path, HTTP_USER_AGENT=ua).content.decode()
                    without_nonce = lambda value: re.sub(r'nonce="[^"]+"', 'nonce=""', value)
                    self.assertEqual(without_nonce(bot_html), without_nonce(html))
                ld = re.search(r'data-seo-jsonld="true">(.*?)</script>', html, re.S)
                json.loads(ld[1])

    def test_threshold_four_five_and_block(self):
        self.assertEqual(self.payload('/anime/genre/small')['robots'], 'noindex,follow')
        fifth = Anime.objects.order_by('pk')[4]
        fifth.genres = ['Романтика', 'Редкий']
        fifth.save()
        self.assertEqual(self.payload('/anime/genre/small')['robots'], 'index,follow')
        CatalogVisibility.objects.create(anime=fifth, manual_hidden=True)
        data = self.payload('/anime/genre/small')
        self.assertEqual(data['count'], 4)
        self.assertEqual(data['robots'], 'noindex,follow')
        self.assertNotIn(fifth.title_ru, data['contentHtml'])

    def test_real_filters_stable_pagination(self):
        first = self.payload('/anime/collection/romance-2025')
        second = self.payload('/anime/collection/romance-2025?page=2')
        self.assertEqual(first['count'], 30)
        self.assertEqual(len(first['items']), 24)
        self.assertEqual(len(second['items']), 6)
        self.assertTrue(second['canonical'].endswith('?page=2'))
        self.assertNotEqual(first['title'], second['title'])
        self.assertIn('rel="next"', first['contentHtml'])
        self.assertEqual(first['items'], self.payload('/anime/collection/romance-2025')['items'])
        self.assertFalse({x['path'] for x in first['items']} & {x['path'] for x in second['items']})
        self.assertEqual(self.get('/anime/year/2025?page=99').status_code, 404)

    def test_collection_refinements_match_html_and_keep_fixed_selection(self):
        base = '/anime/collection/romance-2025'
        data = self.payload(base + '?page_size=20&page=2&ordering=title_ru')
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['page_size'], 20)
        self.assertTrue(data['canonical'].endswith(base))
        self.assertIn('page_size=20', data['previous_url'])
        self.assertEqual(len(data['items']), 10)
        self.assertEqual(data['robots'], 'noindex,follow')
        self.assertIn(data['items'][0]['name'], self.get(base + '?page_size=20&page=2&ordering=title_ru').content.decode())
        filtered = self.payload(base + '?genres=Редкий')
        self.assertEqual(filtered['count'], 4)
        self.assertTrue(all(item['year'] == 2025 and 'Редкий' in item['genres'] for item in filtered['items']))
        self.assertEqual(self.payload(base + '?year_from=2026')['count'], 0)
        self.assertEqual(self.payload(base + '?type=movie')['count'], 0)
        self.assertEqual(self.payload(base + '?status=announced')['count'], 0)
        self.assertEqual(self.payload(base + '?search=несуществующее')['count'], 0)
        first = self.payload(base + '?shuffle=true&shuffle_seed=fixed')
        second = self.payload(base + '?shuffle=true&shuffle_seed=fixed&page=2')
        self.assertEqual(first['items'], self.payload(base + '?shuffle=true&shuffle_seed=fixed')['items'])
        self.assertFalse({item['id'] for item in first['items']} & {item['id'] for item in second['items']})
        self.assertEqual(len(first['items']) + len(second['items']), 30)
        self.assertEqual(self.payload(base + '?score_from=NaN&episodes_to=inf')['status'], 200)
        Anime.objects.filter(pk__in=list(Anime.objects.order_by('pk').values_list('pk', flat=True)[:6])).update(year=2024)
        self.assertEqual(len(self.payload(base + '?page_size=20&page=2')['items']), 4)

    def test_collection_library_exclusion_uses_current_account(self):
        from apps.users.infrastructure.models.users import UserLibrary
        from rest_framework_simplejwt.tokens import AccessToken
        UserLibrary.objects.create(user=self.user, anime=self.anime, status='completed')
        path = '/anime/year/2025?excluded_library_statuses=completed'
        self.assertEqual(self.payload(path)['count'], 30)
        response = self.get('/api/seo/page/', data={'path': path}, HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(self.user)}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 29)
        self.assertNotIn(self.anime.pk, [item['id'] for item in response.json()['items']])
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(self.payload(path)['count'], 30)

    def test_browse_is_a_single_directory_without_catalog_cards(self):
        Anime.objects.create(title_ru='Редкое аниме 2016', slug='rare-2016', has_cyrillic=True,
            year=2016, kind='movie', status='finished', episodes=1, genres=['Редкий'], release_date=date(2016, 7, 1))
        data = self.payload('/anime/browse')
        self.assertEqual(data['items'], [])
        self.assertEqual(data['count'], len(data['related']))
        self.assertGreater(data['count'], 0)
        self.assertEqual(data['pages'], 1)
        self.assertEqual(data['number'], 1)
        self.assertEqual(data['next_url'], '')
        self.assertEqual(data['previous_url'], '')
        self.assertNotIn('/anime/browse', [link['path'] for link in data['related']])
        paths = [link['path'] for link in data['related']]
        self.assertIn('/anime/year/2016', paths)
        self.assertIn('/anime/genre/small', paths)
        for prefix in ['/anime/year/', '/anime/genre/', '/anime/season/', '/anime/type/', '/anime/status/', '/anime/collection/']:
            self.assertTrue(any(path.startswith(prefix) for path in paths), prefix)

    def test_browse_contains_every_visible_year_without_a_popularity_threshold(self):
        for year in [1943, 1957, 1988, 2016]:
            Anime.objects.create(title_ru=f'Единственное аниме {year}', slug=f'only-{year}', has_cyrillic=True,
                year=year, kind='movie', status='released', genres=['Романтика'])
        data = self.payload('/anime/browse')
        listed = {int(link['path'].rsplit('/', 1)[1]) for link in data['related'] if link['path'].startswith('/anime/year/')}
        expected = set(Anime.objects.filter(is_available=True, has_cyrillic=True).exclude(title_ru='')
                       .exclude(year=None).values_list('year', flat=True))
        self.assertEqual(listed, expected)

    def test_forbidden_facets_never_leak_and_their_pages_are_blocked(self):
        forbidden = Genre.objects.create(name='Запрещённый жанр', slug='forbidden')
        restored = Anime.objects.create(title_ru='Редакторское исключение', slug='restored-forbidden',
            has_cyrillic=True, year=2025, kind='music', status='released', genres=[forbidden.name])
        CatalogVisibility.objects.create(anime=restored, restored=True)
        CatalogHideRule.objects.create(rule_type='genre', value=forbidden.name)
        CatalogHideRule.objects.create(rule_type='kind', value='music')

        browse = self.payload('/anime/browse')
        self.assertNotIn(forbidden.name, [link['name'] for link in browse['related']])
        self.assertNotIn('/anime/type/music', [link['path'] for link in browse['related']])
        self.assertNotIn(forbidden.name, self.get('/api/anime/genres/').json()['genres'])
        self.assertNotIn('music', self.get('/api/anime/types/').json()['types'])
        self.assertEqual(self.get('/anime/genre/forbidden').status_code, 404)
        self.assertEqual(self.get('/anime/type/music').status_code, 404)
        self.assertEqual(self.get('/api/anime/', data={'genres': forbidden.name}).json()['count'], 0)
        self.assertEqual(self.get('/api/anime/', data={'type': 'music'}).json()['count'], 0)

    def test_finished_status_includes_both_provider_status_names(self):
        released = Anime.objects.create(title_ru='Выпущенное аниме', slug='released-title', has_cyrillic=True,
            year=2025, kind='tv', status='released', genres=['Романтика'])
        data = self.payload('/anime/status/finished')
        self.assertIn(released.pk, [item['id'] for item in data['items']] + [
            item['id'] for item in self.payload('/anime/status/finished?page=2')['items']
        ])
        self.assertEqual(data['count'], 31)
        self.assertEqual(self.get('/api/anime/', data={'status': 'finished', 'page_size': 100}).json()['count'], 31)
        self.assertEqual(self.get('/anime/status/released').status_code, 301)
        self.assertTrue(self.get('/anime/status/released')['Location'].endswith('/anime/status/finished'))

    def test_franchise_directory_and_two_part_franchises_are_indexable(self):
        compact = Franchise.objects.create(name='Короткая франшиза', slug='compact-franchise')
        for index in range(2):
            Anime.objects.create(title_ru=f'Короткая часть {index + 1}', slug=f'compact-part-{index + 1}',
                has_cyrillic=True, year=2020 + index, kind='movie', status='released',
                genres=['Экшен'], franchise=compact, franchise_order=index)
        detail = self.payload('/franchise/compact-franchise')
        self.assertEqual(detail['robots'], 'index,follow')
        self.assertIn('порядок просмотра', detail['title'])
        self.assertIn('2 части', detail['text'])
        directory = self.payload('/anime/franchises')
        self.assertIn('/franchise/compact-franchise', [item['path'] for item in directory['items']])
        self.assertEqual(directory['robots'], 'index,follow')
    def test_genre_pages_do_not_depend_on_relational_genre_rows(self):
        with self.captureOnCommitCallbacks(execute=True):
            Anime.objects.create(title_ru='Экшен без справочника', slug='action-without-row', has_cyrillic=True,
                year=2025, kind='movie', status='released', genres=['Экшен'])
        data = self.payload('/anime/genre/ekshen')
        self.assertEqual(data['status'], 200)
        self.assertIn('Экшен', data['h1'])

    def test_thin_public_user_content_stays_out_of_index(self):
        user = get_user_model().objects.create_user(username='thin-user', nickname='thin', bio='Коротко')
        post = Post.objects.create(author=user, text='Короткая запись')
        playlist = Playlist.objects.create(user=user, title='Пустой список', description='Пара слов')
        self.assertEqual(self.payload('/@thin')['robots'], 'noindex,follow')
        self.assertEqual(self.payload(f'/post/{post.public_id}')['robots'], 'noindex,follow')
        self.assertEqual(self.payload(f'/playlist/{playlist.pk}')['robots'], 'noindex,follow')
        self.assertNotIn('/@thin', self.get('/sitemap-profiles-1.xml').content.decode())
        self.assertNotIn(str(post.public_id), self.get('/sitemap-posts-1.xml').content.decode())
        self.assertNotIn(str(playlist.pk), self.get('/sitemap-playlists-1.xml').content.decode())

    def test_unknown_paths_and_invalid_pagination(self):
        for path in ['/unknown/does-not-exist', '/anime/year/1880', '/anime/genre/absent', '/anime/studio/test',
                     '/anime/year/2025?page=0', '/anime/year/2025?page=x', '/anime/year/2025?page=2&page=3',
                     '/anime/99999999-absent', anime_path(self.anime) + '?page=2']:
            self.assertEqual(self.get(path).status_code, 404, path)
        html = self.get('/unknown/does-not-exist').content.decode()
        self.assertNotIn('rel="canonical"', html)
        self.assertNotIn('property="og:url"', html)
        self.assertEqual(self.payload('/unknown/does-not-exist')['schema'], [])

    def test_canonical_and_redirects(self):
        response = self.get('/anime/' + self.anime.slug + '/?page=1&utm_source=x')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://catalog.example.org' + anime_path(self.anime))
        response = self.get('/anime/calendar?page=1&utm_source=x')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://catalog.example.org/anime?section=calendar')
        response = self.get('/anime/status/released?page=2')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://catalog.example.org/anime/status/finished?page=2')
        self.assertEqual(self.get('/unknown/does-not-exist/?page=1').status_code, 404)
        self.assertEqual(self.get('/anime?utm_source=x').status_code, 200)
        self.assertEqual(self.payload('/anime?utm_source=x')['canonical'], 'https://catalog.example.org/anime')
        self.assertEqual(self.payload('/anime?search=romance')['robots'], 'noindex,follow')
        self.assertEqual(self.payload('/anime/year/2025?sort=random')['robots'], 'noindex,follow')
        response = self.client.get(anime_path(self.anime), HTTP_HOST='www.catalog.example.org')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://catalog.example.org' + anime_path(self.anime))

    def test_changed_slug_has_one_hop_alias(self):
        old = self.anime.slug
        self.anime.slug = 'renamed'
        self.anime.save()
        response = self.get('/anime/' + old)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].endswith(anime_path(self.anime)))
        self.assertEqual(self.get('/api/anime/' + old + '/').status_code, 200)
        Anime.objects.filter(pk=self.anime.pk).update(is_available=False)
        self.assertEqual(self.get('/api/anime/' + old + '/').status_code, 404)

    def test_numeric_legacy_slug_is_not_another_anime_id(self):
        slug = f'{self.anime.pk}-legacy-title'
        owner = Anime.objects.create(title_ru='Тайтл с числом в старом slug', slug=slug)
        response = self.get('/anime/' + slug)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://catalog.example.org' + anime_path(owner))
        self.assertEqual(self.get('/api/anime/' + slug + '/').json()['id'], owner.pk)
        Anime.objects.filter(pk=owner.pk).update(is_available=False)
        self.assertEqual(self.get('/anime/' + slug).status_code, 404)
        self.assertEqual(self.get('/api/anime/' + slug + '/').status_code, 404)

    def test_private_post_group_playlist_and_secret_never_projected(self):
        self.payload(f'/post/{self.post.public_id}')
        Post.objects.filter(pk=self.post.pk).update(visibility='private')
        self.assertEqual(self.get(f'/post/{self.post.public_id}').status_code, 404)
        self.assertNotIn(self.post.text, self.get(f'/post/{self.post.public_id}').content.decode())
        Post.objects.filter(pk=self.post.pk).update(visibility='public')
        group = Group.objects.create(name='Закрытая группа', slug='closed', creator=self.user, is_private=True)
        Post.objects.filter(pk=self.post.pk).update(group=group)
        self.assertEqual(self.get(f'/post/{self.post.public_id}').status_code, 404)
        for visibility in ['private', 'link']:
            Playlist.objects.filter(pk=self.playlist.pk).update(visibility=visibility)
            response = self.get(f'/playlist/{self.playlist.pk}')
            self.assertEqual(response.status_code, 404)
            self.assertNotIn(self.playlist.title, response.content.decode())
        response = self.get('/playlist/shared/secret-token')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.playlist.title, response.content.decode())
        self.assertIn('noindex,follow', response.content.decode())
        self.assertNotIn('secret-token', response.content.decode())

    def test_deleted_and_unpublished_post_removed_immediately(self):
        for status in ['draft', 'processing', 'failed', 'moderated', 'deleted']:
            Post.objects.filter(pk=self.post.pk).update(status=status)
            self.assertEqual(self.get(f'/post/{self.post.public_id}').status_code, 404)
        self.post.delete()
        self.assertEqual(self.get(f'/post/{self.post.public_id}').status_code, 404)

    def test_blocked_details_and_franchise_do_not_leak(self):
        self.get(anime_path(self.anime))
        Anime.objects.filter(pk=self.anime.pk).update(is_available=False)
        self.assertEqual(self.get(anime_path(self.anime)).status_code, 404)
        self.assertEqual(self.get(f'/api/anime/{self.anime.pk}/').status_code, 404)
        self.assertNotIn(self.anime.title_ru, self.payload('/franchise/public-franchise')['contentHtml'])
        CatalogHideRule.objects.create(rule_type='title', value='Тестовое')
        self.assertEqual(self.payload('/anime')['count'], 0)
        self.assertEqual(self.get('/franchise/public-franchise').status_code, 404)

    def test_safe_json_and_no_fabricated_ratings(self):
        self.anime.description = '</script><script>alert(1)</script> Текст & данные'
        self.anime.score = 9.9
        self.anime.save()
        html = self.get(anime_path(self.anime)).content.decode()
        self.assertNotIn('<script>alert(1)', html)
        self.assertNotIn('ratingCount', html)
        self.assertNotIn('aggregateRating', html)
        self.assertNotIn('VideoObject', html)

    def test_settings_override_and_import_are_live(self):
        config = SiteSeoSettings.objects.create(site_name='Новое имя', public_origin='https://catalog.example.org', indexing_enabled=True,
            templates={'anime': {'title': '{name}: {site}', 'description': '{summary}'}})
        self.assertIn('Новое имя', self.payload(anime_path(self.anime))['title'])
        SeoOverride.objects.create(path=anime_path(self.anime), title='Ручной заголовок')
        self.assertEqual(self.payload(anime_path(self.anime))['title'], 'Ручной заголовок')
        Anime.objects.filter(pk=self.anime.pk).update(description='Новое описание после импорта')
        self.assertIn('Новое описание', self.payload(anime_path(self.anime))['description'])
        config.indexing_enabled = False
        config.save()
        self.assertEqual(self.payload(anime_path(self.anime))['robots'], 'noindex,follow')
        config.templates = {'anime': {'title': '{name.__class__}'}}
        self.assertRaises(ValidationError, config.full_clean)

    def test_sitemap_xml_live_visibility_threshold_and_lastmod(self):
        SeoHub.objects.all().delete()
        self.assertEqual(self.get('/sitemap-hubs-1.xml').status_code, 404)
        self.assertNotIn('sitemap-hubs-1.xml', self.get('/sitemap.xml').content.decode())
        refresh_hubs()
        response = self.get('/sitemap.xml')
        root = ElementTree.fromstring(response.content)
        self.assertIn('sitemapindex', root.tag)
        locations = []
        for element in root.iter():
            if element.tag.endswith('loc'):
                response = self.get(element.text.removeprefix('https://catalog.example.org'))
                locations += [node.text for node in ElementTree.fromstring(response.content).iter() if node.tag.endswith('loc')]
        self.assertIn('https://catalog.example.org' + anime_path(self.anime), locations)
        self.assertNotIn('https://catalog.example.org/anime/genre/small', locations)
        first = self.get('/sitemap-anime-1.xml').content
        self.assertEqual(first, self.get('/sitemap-anime-1.xml').content)
        Anime.objects.filter(pk=self.anime.pk).update(is_available=False)
        self.assertNotIn(anime_path(self.anime).encode(), self.get('/sitemap-anime-1.xml').content)
        Playlist.objects.filter(pk=self.playlist.pk).update(visibility='private')
        self.assertNotIn(self.playlist.pk.encode(), self.get('/sitemap-playlists-1.xml').content)
        Post.objects.filter(pk=self.post.pk).update(is_deleted=True)
        self.assertNotIn(str(self.post.public_id).encode(), self.get('/sitemap-posts-1.xml').content)

    @override_settings(SEO_INDEXING_ENABLED=False, SEO_PUBLIC_ORIGIN='')
    def test_local_is_noindex_and_sitemap_empty(self):
        self.assertIn('noindex,follow', self.get('/').content.decode())
        self.assertIn('Disallow: /', self.get('/robots.txt').content.decode())
        self.assertNotIn('<loc>', self.get('/sitemap.xml').content.decode())

    def test_metadata_matches_html_and_api(self):
        Anime.objects.filter(pk=self.anime.pk).update(poster_url='https://cdn.example.org/poster.jpg')
        data = self.payload(anime_path(self.anime))
        html = self.get(anime_path(self.anime)).content.decode()
        self.assertIn('<title>' + data['title'] + '</title>', html)
        self.assertIn(data['contentHtml'], html)
        self.assertIn(data['canonical'], html)
        self.assertIn('property="og:image:alt"', html)
        self.assertIn('name="twitter:image:alt"', html)
        item = self.payload('/anime/year/2025')['items'][0]
        self.assertEqual(item['id'], self.anime.pk)
        self.assertEqual(item['type'], 'tv')
        self.assertEqual(item['status'], 'finished')
        self.assertEqual(item['genres'], ['Романтика', 'Редкий'])
        for path in ['/', '/anime']:
            self.assertFalse(any('mainEntity' in schema for schema in self.payload(path)['schema']))

    def test_public_post_api_matches_document_access(self):
        path = f'/api/social/posts/{self.post.public_id}/public/'
        self.assertEqual(self.get(path).status_code, 200)
        Post.objects.filter(pk=self.post.pk).update(visibility='private')
        self.assertIn(self.get(path).status_code, (403, 404))
        Post.objects.filter(pk=self.post.pk).update(visibility='followers')
        self.assertIn(self.get(path).status_code, (403, 404))

    def test_invalid_collection_conditions_rejected(self):
        for conditions in [{'studio': 'secret'}, {}, {'year': '2025'}, {'season': 'winter'}, {'kind': 'bad'}]:
            collection = SeoCollection(slug='invalid', name='Invalid', filters=conditions)
            self.assertRaises(ValidationError, collection.full_clean)

    def test_interactive_catalog_is_noindex_with_clean_canonical(self):
        data = self.payload('/anime?section=catalog')
        self.assertEqual(data['robots'], 'noindex,follow')
        self.assertEqual(data['canonical'], 'https://catalog.example.org/anime')
        response = self.get('/admin/franchises')
        self.assertEqual(response.status_code, 200)
        self.assertIn('noindex,follow', response.content.decode())

    def test_stale_hub_inventory_rechecks_five_to_four(self):
        fifth = Anime.objects.order_by('pk')[4]
        fifth.genres = ['Романтика', 'Редкий']
        fifth.save()
        refresh_hubs()
        self.assertIn(b'/anime/genre/small', self.get('/sitemap-hubs-1.xml').content)
        Anime.objects.filter(pk=fifth.pk).update(is_available=False)
        self.assertNotIn(b'/anime/genre/small', self.get('/sitemap-hubs-1.xml').content)

    @patch('apps.seo.service.feature_flags.FEATURE_DUBS_ENABLED', True)
    def test_other_existing_public_routes_have_real_status_and_content(self):
        from apps.dubs.infrastructure.models.dubs import Person
        from apps.anime.infrastructure.models.anime import AnimeAnnouncement
        person = Person.objects.create(name='Публичный сейю', slug='public-person', description='Биография персоны')
        response = self.get(f'/people/{person.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Биография персоны', response.content.decode())
        announcement = AnimeAnnouncement.objects.create(title_ru='Публичный анонс', slug='public-announcement', description='Текст анонса')
        response = self.get('/announcements/public-announcement')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Текст анонса', response.content.decode())
        self.assertEqual(response['X-Robots-Tag'], 'noindex,follow')
        CatalogHideRule.objects.create(rule_type='title', value='Публичный анонс')
        self.assertEqual(self.get('/announcements/public-announcement').status_code, 404)

    @patch('apps.seo.service.feature_flags.FEATURE_DUBS_ENABLED', False)
    def test_disabled_people_detail_matches_frontend_404(self):
        from apps.dubs.infrastructure.models.dubs import Person
        person = Person.objects.create(name='Скрытая персона', description='Не должна иметь SEO shell')
        self.assertEqual(self.get(f'/people/{person.pk}').status_code, 404)

    def test_auth_callback_routes_are_real_noindex_documents(self):
        for path in ['/confirm-email?token=secret', '/reset-password?token=secret', '/oauth/callback?code=secret']:
            response = self.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['X-Robots-Tag'], 'noindex,follow')
            self.assertNotIn('secret', response.content.decode())

    def test_home_schema_has_stable_site_identity_without_fabricated_contacts(self):
        schema = self.payload('/')['schema']
        website = next(item for item in schema if item['@type'] == 'WebSite')
        organization = next(item for item in schema if item['@type'] == 'Organization')
        self.assertEqual(website['@id'], 'https://catalog.example.org/#website')
        self.assertEqual(website['publisher'], {'@id': 'https://catalog.example.org/#organization'})
        self.assertEqual(organization['logo']['url'], 'https://catalog.example.org/pwa/icon-512.png')
        self.assertNotIn('email', organization)
        self.assertNotIn('sameAs', organization)
