import asyncio
import hashlib
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

from asgiref.sync import async_to_sync
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from datetime import timedelta

from core.socket_auth import SocketAuthBatcher, credential, validate_batch
from apps.users.infrastructure.models.users import User, ActiveSession


class SocketAuthDatabaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create([User(username=f'capacity-{i}', email=f'capacity-{i}@example.test', password='!') for i in range(40)])
        cls.users = list(User.objects.filter(username__startswith='capacity-').order_by('pk'))
        cls.keys = {user.pk: hashlib.sha256(str(user.pk).encode()).hexdigest()[:32] for user in cls.users}
        Session.objects.bulk_create([Session(session_key=cls.keys[user.pk], expire_date=timezone.now() + timedelta(hours=1),
            session_data=SessionStore().encode({'_auth_user_id': str(user.pk), '_auth_user_hash': user.get_session_auth_hash()})) for user in cls.users])
        ActiveSession.objects.bulk_create([ActiveSession(user=user, session_key=cls.keys[user.pk], ip_address='127.0.0.1', user_agent='test') for user in cls.users])
        cls.selectors = dict(ActiveSession.objects.filter(user__in=cls.users).values_list('user_id', 'pk'))

    def claims(self, user):
        return {'sid': str(self.selectors[user.pk]), 'exp': time.time() + 3600}

    def test_forty_current_sessions_need_two_queries(self):
        records = [credential(user.pk, self.claims(user)) for user in self.users]
        with self.assertNumQueries(2):
            results = validate_batch(records)
        self.assertEqual({result.pk for result in results.values()}, {user.pk for user in self.users})

    def test_deleted_session_is_rejected_on_the_very_next_check(self):
        user = self.users[0]
        record = credential(user.pk, self.claims(user))
        self.assertIsNotNone(validate_batch([record])[record])
        Session.objects.filter(session_key=self.keys[user.pk]).delete()
        self.assertIsNone(validate_batch([record])[record])

    def test_disabled_account_and_changed_password_are_rejected(self):
        first, second = self.users[:2]
        records = [credential(user.pk, self.claims(user)) for user in (first, second)]
        User.objects.filter(pk=first.pk).update(is_active=False)
        User.objects.filter(pk=second.pk).update(password='changed')
        self.assertEqual(list(validate_batch(records).values()), [None, None])

    def test_selector_cannot_be_used_by_another_user(self):
        first, second = self.users[:2]
        record = credential(first.pk, self.claims(second))
        self.assertIsNone(validate_batch([record])[record])

    def test_cookie_session_obeys_expiry_and_password_hash(self):
        user = self.users[0]
        record = credential(user.pk, cookie=self.keys[user.pk])
        self.assertIsNotNone(validate_batch([record])[record])
        Session.objects.filter(session_key=self.keys[user.pk]).update(expire_date=timezone.now() - timedelta(seconds=1))
        self.assertIsNone(validate_batch([record])[record])

    def test_legacy_tokens_obey_version_revocation(self):
        user = self.users[0]
        record = credential(user.pk, {'exp': time.time() + 3600, 'ver': user.token_version})
        self.assertIsNotNone(validate_batch([record])[record])
        User.objects.filter(pk=user.pk).update(token_version=user.token_version + 1)
        self.assertIsNone(validate_batch([record])[record])

    def test_expiry_is_checked_again_when_the_batch_runs(self):
        user = self.users[0]
        record = credential(user.pk, {'exp': time.time() + 3600})
        expired = type(record)(record.user_id, record.selector, record.version, record.cookie, time.time() - 1)
        self.assertIsNone(validate_batch([expired])[expired])


class SocketAuthSchedulingTests(SimpleTestCase):
    def test_burst_is_bounded_and_coalesced_without_reusing_later_decisions(self):
        async def run():
            async def validate(records):
                return {record: SimpleNamespace(pk=record.user_id) for record in records}
            validator = AsyncMock(side_effect=validate)
            batcher = SocketAuthBatcher(validator)
            records = [credential(i + 1, {'exp': time.time() + 3600}) for i in range(300)]
            values = await asyncio.gather(*(batcher.check(record) for record in records))
            self.assertEqual(len(values), 300)
            self.assertEqual(validator.await_count, 3)
            self.assertTrue(all(len(call.args[0]) <= 128 for call in validator.await_args_list))
            validator.side_effect = None
            validator.return_value = {}
            self.assertIsNone(await batcher.check(records[0]))
            self.assertEqual(validator.await_count, 4)
        async_to_sync(run)()

    def test_cancellation_and_unavailable_database_do_not_grant_access(self):
        async def run():
            validator = AsyncMock(side_effect=RuntimeError('database unavailable'))
            batcher = SocketAuthBatcher(validator, max_pending=2)
            record = credential(1, {'exp': time.time() + 3600})
            cancelled = asyncio.create_task(batcher.check(record))
            await asyncio.sleep(0)
            cancelled.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await cancelled
            self.assertIsNone(await batcher.check(record))
        async_to_sync(run)()

    def test_bad_or_expired_credentials_never_enter_a_batch(self):
        for token in ({'exp': 0}, {'exp': float('nan')}, {'exp': time.time() + 60, 'sid': 'invalid'}, {'exp': time.time() + 60, 'sid': str(2**64)}):
            self.assertIsNone(credential(1, token))
        self.assertIsNone(credential(None))
