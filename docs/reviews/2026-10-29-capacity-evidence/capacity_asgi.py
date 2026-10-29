import json,os,resource,threading,time,faulthandler,signal
import requests
import cProfile,pstats
from config.asgi import application as base
from django.db.backends.signals import connection_created
from django.db import connections
from core import socket_auth
from asgiref.sync import SyncToAsync
from channels.db import DatabaseSyncToAsync
faulthandler.register(signal.SIGUSR1,all_threads=True)

def no_http(*args,**kwargs):raise RuntimeError('External provider HTTP is disabled in the capacity test')
requests.sessions.Session.request=no_http
lock=threading.Lock();counts={'sql':0,'auth_batches':0,'auth_records':0}
def count_sql(execute,sql,params,many,context):
 with lock:counts['sql']+=1
 return execute(sql,params,many,context)
def new_connection(sender,connection,**kwargs):
 # Django reopens the same connection object; wrappers survive close().
 if count_sql not in connection.execute_wrappers:connection.execute_wrappers.append(count_sql)
connection_created.connect(new_connection,weak=False)
original=socket_auth.validate_batch
def validate(records):
 with lock:counts['auth_batches']+=1;counts['auth_records']+=len(records)
 return original(records)
socket_auth.validate_batch=validate
profile=None
worker_profile_enabled=False
worker_profiles=None
profiling_thread=threading.local()
def measured_handler(original):
 def measured(self,*args,**kwargs):
  global worker_profiles
  if not worker_profile_enabled or getattr(profiling_thread,'active',False):return original(self,*args,**kwargs)
  profiling_thread.active=True;sample=cProfile.Profile();sample.enable()
  try:return original(self,*args,**kwargs)
  finally:
   sample.disable();profiling_thread.active=False
   with lock:
    if worker_profiles is None:worker_profiles=pstats.Stats(sample)
    else:worker_profiles.add(sample)
 return measured
SyncToAsync.thread_handler=measured_handler(SyncToAsync.thread_handler)
DatabaseSyncToAsync.thread_handler=measured_handler(DatabaseSyncToAsync.thread_handler)
async def application(scope,receive,send):
 global profile,worker_profile_enabled,worker_profiles
 if scope['type']=='http' and scope['path'].startswith('/__capacity_'):
  result={'identity':'animecore-capacity-isolated','node':os.environ.get('CAPACITY_NODE','unknown')}
  if scope['path']=='/__capacity_profile_start':
   profile=cProfile.Profile();profile.enable()
   worker_profiles=None;worker_profile_enabled=True
  if scope['path']=='/__capacity_profile_stop' and profile:
   profile.disable();stats=pstats.Stats(profile)
   worker_profile_enabled=False
   result['profile']=[{'function':f'{key[0]}:{key[1]}:{key[2]}','calls':value[1],'self_ms':value[2]*1000,'cumulative_ms':value[3]*1000} for key,value in sorted(stats.stats.items(),key=lambda row:row[1][2],reverse=True)[:25]]
   if worker_profiles:
    with lock:worker_items=list(worker_profiles.stats.items())
    result['worker_profile']=[{'function':f'{key[0]}:{key[1]}:{key[2]}','calls':value[1],'self_ms':value[2]*1000,'cumulative_ms':value[3]*1000} for key,value in sorted(worker_items,key=lambda row:row[1][2],reverse=True)[:35]]
  if scope['path']=='/__capacity_metrics':
   with lock:result.update(counts)
   result.update(max_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,threads=threading.active_count(),cpu_seconds=time.process_time(),active=dict(base.active),pending_handshakes=base.pending_handshakes,sync_queue=SyncToAsync.single_thread_executor._work_queue.qsize())
  await send({'type':'http.response.start','status':200,'headers':[(b'content-type',b'application/json')]})
  await send({'type':'http.response.body','body':json.dumps(result).encode()})
  return
 return await base(scope,receive,send)
