#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
from apps.social.infrastructure.models.social import UUIDv8Model, PrivateChat, GroupChat

def backfill():
    for model in (PrivateChat, GroupChat):
        null_qs = model.objects.filter(public_id__isnull=True)
        for obj in null_qs.iterator(chunk_size=200):
            from apps.social.infrastructure.models.social import generate_public_id
            obj.public_id = generate_public_id()
            tries = 0
            while model.objects.filter(public_id=obj.public_id).exclude(pk=obj.pk).exists() and tries < 10:
                obj.public_id = generate_public_id()
                tries += 1
            obj.save(update_fields=['public_id'])
    print('CHAT-003 backfill done.')

if __name__ == '__main__':
    backfill()
