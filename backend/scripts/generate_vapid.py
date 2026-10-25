#!/usr/bin/env python3
from pywebpush import generate_vapid_keys
keys = generate_vapid_keys()
print('VAPID_PUBLIC_KEY=', keys['public'])
print('VAPID_PRIVATE_KEY=', keys['private'])
print('Add VAPID_SUBJECT=https://yourdomain.com (or mailto:)')
