"""Migration rehearsal against the restored local backup, isolated DB/Redis."""
from performance_settings import *
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ['SECRET_KEY']
