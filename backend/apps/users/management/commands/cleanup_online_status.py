#!/usr/bin/env python
import os
import sys
import django
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Clean up online status for inactive users'

    def handle(self, *args, **options):
        cutoff_time = timezone.now() - timedelta(minutes=5)

        online_users = User.objects.filter(is_online=True)

        updated_count = 0
        for user in online_users:
            should_set_offline = False

            if user.last_seen and user.last_seen < cutoff_time:
                should_set_offline = True
            elif not user.last_seen:
                has_recent_session = False
                if hasattr(user, 'active_sessions'):
                    has_recent_session = user.active_sessions.filter(
                        last_activity__gte=cutoff_time
                    ).exists()

                if not has_recent_session:
                    should_set_offline = True

            if should_set_offline:
                user.is_online = False
                user.save(update_fields=['is_online'])
                updated_count += 1
                self.stdout.write(f'Set offline: {user.username}')

        self.stdout.write(
            self.style.SUCCESS(f'Updated online status for {updated_count} users')
        )