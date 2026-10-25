import json
import threading
import time
import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple
import redis
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._callbacks: Dict[str, List[Tuple[Callable, Optional[asyncio.AbstractEventLoop]]]] = defaultdict(list)
        self._callbacks_lock = threading.Lock()
        self._redis_client = None
        self._pubsub_client = None
        self._pubsub = None
        self._listener_thread = None
        self._should_run = True
        self._connected = threading.Event()
        self._reconnect_delay = 5

    def register_callback(self, channel: str, callback: Callable, loop: Optional[asyncio.AbstractEventLoop] = None):
        with self._callbacks_lock:
            self._callbacks[channel].append((callback, loop))

    def unregister_callback(self, channel: str, callback: Callable):
        with self._callbacks_lock:
            if channel in self._callbacks:
                self._callbacks[channel] = [
                    (cb, loop) for cb, loop in self._callbacks[channel] if cb != callback
                ]

    def _get_redis_client(self):
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=getattr(settings, "REDIS_SOCKET_TIMEOUT", 2),
                retry_on_timeout=False,
            )
        return self._redis_client

    def _get_pubsub_client(self):
        if self._pubsub_client is None:
            self._pubsub_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=None,
                retry_on_timeout=False,
            )
        return self._pubsub_client

    def _listen(self):
        while self._should_run:
            try:
                client = self._get_pubsub_client()
                client.ping()

                pubsub = client.pubsub()
                pubsub.subscribe("realtime_updates")
                self._pubsub = pubsub
                self._connected.set()
                self._reconnect_delay = 5

                for message in pubsub.listen():
                    if not self._should_run:
                        break
                    if message["type"] == "message":
                        try:
                            event = json.loads(message["data"])
                            self._dispatch(event)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in Redis message: {e}")
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {e}")

            except redis.ConnectionError as e:
                logger.warning(f"Redis connection lost: {e}. Reconnecting in {self._reconnect_delay} seconds...")
                self._connected.clear()
                self._pubsub_client = None
                self._pubsub = None
                time.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)
            except Exception as e:
                logger.error(f"Redis listener error: {e}. Reconnecting in {self._reconnect_delay} seconds...")
                self._connected.clear()
                self._pubsub_client = None
                self._pubsub = None
                time.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    def is_connected(self):
        return self._connected.is_set()

    def _dispatch(self, event: dict):
        with self._callbacks_lock:
            callbacks = list(self._callbacks.get("realtime_updates", []))

        for callback, loop in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    if loop is None or loop.is_closed() or not loop.is_running():
                        logger.warning("Event loop not available for async callback")
                        continue
                    asyncio.run_coroutine_threadsafe(callback(event), loop)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error dispatching event to callback: {e}")

    def start(self):
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._should_run = True
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()

    def stop(self):
        self._should_run = False
        if self._pubsub:
            try:
                self._pubsub.close()
            except Exception:
                pass
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception:
                pass
        if self._pubsub_client:
            try:
                self._pubsub_client.close()
            except Exception:
                pass

    def wait_connected(self, timeout=10):
        return self._connected.wait(timeout)

    def publish(self, event: dict):
        try:
            client = self._get_redis_client()
            client.publish("realtime_updates", json.dumps(event))
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")


redis_pubsub_manager = RedisPubSubManager()
