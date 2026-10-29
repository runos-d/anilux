import json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
base='http://127.0.0.1:4387'
def request(path):
 start=time.perf_counter()
 try: response=urllib.request.urlopen(base+path,timeout=8)
 except urllib.error.HTTPError as error:response=error
 with response:
  body=response.read()
  return {'status':response.status,'ms':round((time.perf_counter()-start)*1000,2),'retryAfter':response.headers.get('Retry-After')}
assert json.load(urllib.request.urlopen(base+'/__audit_identity'))['audit']=='animecore-fix-verification'
mode=sys.argv[1];result={'ready':request('/health/ready/'),'live':request('/health/live/'),'apiFirst':request('/api/anime/?page_size=20'),'apiSecond':request('/api/anime/?page_size=20')}
path=Path(os.environ['AUDIT_RESULT_FILE']);all_results=json.loads(path.read_text()) if path.exists() else {};all_results[mode]=result;path.write_text(json.dumps(all_results,indent=2),encoding='utf-8');print(json.dumps({mode:result}))
if mode=='down':
 assert result['ready']['status']==503 and result['ready']['ms']<4000
 assert result['live']['status']==200
 assert result['apiFirst']['status']==result['apiSecond']['status']==503
 assert result['apiSecond']['ms']<500 and result['apiSecond']['retryAfter']=='5'
else:assert result['ready']['status']==result['apiFirst']['status']==200
