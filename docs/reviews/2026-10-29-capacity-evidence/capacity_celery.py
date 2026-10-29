"""Disposable worker timing only; no task arguments or payloads are logged."""
import json
import time
from celery.signals import task_prerun, task_postrun
from config.celery import app

app.loader.import_default_modules()
from core import group_events
from core.channel_layer import BoundedRedisChannelLayer

started = {}
original_fanout = group_events.send_to_groups
original_send = BoundedRedisChannelLayer.group_send


def emit(**values):
    print('CAPACITY_JOB=' + json.dumps(values), flush=True)


async def fanout(layer, groups, event, **kwargs):
    names = list(groups)
    start = time.perf_counter()
    await original_fanout(layer, names, event, **kwargs)
    emit(part='user_groups', groups=len(names), milliseconds=(time.perf_counter()-start)*1000)


async def group_send(self, group, message):
    start = time.perf_counter()
    result = await original_send(self, group, message)
    if group.startswith('conversation_'):
        emit(part='room', milliseconds=(time.perf_counter()-start)*1000)
    return result


group_events.send_to_groups = fanout
BoundedRedisChannelLayer.group_send = group_send


@task_prerun.connect
def before(task_id, task, **kwargs):
    if task.name.endswith('.deliver_chat_event'):
        started[task_id] = (time.perf_counter(), time.process_time())


@task_postrun.connect
def after(task_id, **kwargs):
    begin = started.pop(task_id, None)
    if begin:
        emit(part='task', milliseconds=(time.perf_counter()-begin[0])*1000,
             cpu_ms=(time.process_time()-begin[1])*1000)
