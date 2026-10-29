"""Coalesce concurrent socket checks; never cache an authorization decision."""
import asyncio
import copy
from collections import deque
from dataclasses import dataclass
import logging
import math
import time
from weakref import WeakKeyDictionary

from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session
from django.db.models import OuterRef, Subquery
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SocketCredential:
    user_id: int
    selector: int | None
    version: int
    cookie: str | None
    expires: float | None


def credential(user_id, token=None, cookie=None):
    try:
        user_id = int(user_id)
        if not 0 < user_id < 2**63:
            return None
        if token is not None:
            expires = float(token.get('exp', 0))
            if not math.isfinite(expires) or expires <= time.time():
                return None
            selector = token.get('sid')
            if selector:
                if not str(selector).isdigit() or not 0 < int(selector) < 2**63:
                    return None
                return SocketCredential(user_id, int(selector), 0, None, expires)
            version = token.get('ver', 0)
            if type(version) is not int:
                return None
            return SocketCredential(user_id, None, version, None, expires)
        if not isinstance(cookie, str) or not 0 < len(cookie) <= 40:
            return None
        return SocketCredential(user_id, None, 0, cookie, None)
    except (ValueError, TypeError, OverflowError):
        return None


def validate_batch(records):
    """Two SQL queries for token batches, three for mixed token/cookie batches."""
    from apps.users.infrastructure.models.users import User, ActiveSession
    users = {user.pk: user for user in User.objects.filter(
        pk__in={record.user_id for record in records}, is_active=True,
    ).order_by()}
    selectors = {record.selector for record in records if record.selector}
    sessions = {}
    if selectors:
        live = Session.objects.filter(session_key=OuterRef('session_key'), expire_date__gt=timezone.now())
        sessions = {pk: (uid, data) for pk, uid, data in ActiveSession.objects.filter(pk__in=selectors).annotate(
            live_data=Subquery(live.values('session_data')[:1]),
        ).order_by().values_list('pk', 'user_id', 'live_data')}
    cookies = {record.cookie for record in records if record.cookie}
    cookie_sessions = dict(Session.objects.filter(
        session_key__in=cookies, expire_date__gt=timezone.now(),
    ).values_list('session_key', 'session_data')) if cookies else {}
    decoded, hashes, result = {}, {}, {}
    for record in records:
        user = users.get(record.user_id)
        allowed = bool(user and (record.expires is None or record.expires > time.time()))
        if allowed and (record.selector or record.cookie):
            owner, encoded = sessions.get(record.selector, (None, None)) if record.selector else (
                record.user_id, cookie_sessions.get(record.cookie),
            )
            if encoded and owner == record.user_id:
                if encoded not in decoded:
                    decoded[encoded] = Session(session_data=encoded).get_decoded()
                if user.pk not in hashes:
                    hashes[user.pk] = user.get_session_auth_hash()
                data = decoded[encoded]
                allowed = str(data.get('_auth_user_id')) == str(user.pk) and data.get('_auth_user_hash') == hashes[user.pk]
            else:
                allowed = False
        elif allowed:
            allowed = record.version == user.token_version
        result[record] = user if allowed else None
    return result


class SocketAuthBatcher:
    def __init__(self, validator=None, batch_size=128, max_pending=32768, flush_delay=0.002, coalesce_between_batches=False):
        self.validator = validator or database_sync_to_async(validate_batch, thread_sensitive=False)
        self.batch_size = batch_size
        self.max_pending = max_pending
        self.flush_delay = flush_delay
        self.coalesce_between_batches = coalesce_between_batches
        self.pending = deque()
        self.scheduled = False
        self.running = False

    async def check(self, record):
        if record is None or len(self.pending) >= self.max_pending:
            return None
        future = asyncio.get_running_loop().create_future()
        self.pending.append((record, future))
        if not self.scheduled and not self.running:
            self.scheduled = True
            asyncio.get_running_loop().call_later(self.flush_delay, self.start)
        return await future

    def start(self):
        self.scheduled = False
        self.running = True
        asyncio.create_task(self.flush())

    async def flush(self):
        first = True
        try:
            while self.pending:
                if not first and self.coalesce_between_batches and len(self.pending) < self.batch_size:
                    await asyncio.sleep(self.flush_delay)
                first = False
                batch = [self.pending.popleft() for _ in range(min(self.batch_size, len(self.pending)))]
                records = {record for record, future in batch if not future.cancelled()}
                try:
                    values = await self.validator(records) if records else {}
                except Exception:
                    logger.warning('Socket authorization batch failed; access denied')
                    values = {}
                for record, future in batch:
                    if not future.done():
                        future.set_result(copy.copy(values[record]) if values.get(record) is not None else None)
        finally:
            self.running = False


_loops = WeakKeyDictionary()


async def socket_user(user_id, token=None, scope=None):
    cookie = getattr((scope or {}).get('session'), 'session_key', None)
    record = credential(user_id, token, cookie)
    if record is None:
        return None
    loop = asyncio.get_running_loop()
    if loop not in _loops:
        _loops[loop] = SocketAuthBatcher()
    return await _loops[loop].check(record)
