import json, os, time, urllib.request, urllib.error
from pathlib import Path
base='http://127.0.0.1:4387'
def get(url, headers=None, payload=None):
    request=urllib.request.Request(url,headers=headers or {},data=None if payload is None else json.dumps(payload).encode())
    try:
        response=urllib.request.urlopen(request,timeout=10)
    except urllib.error.HTTPError as error:
        response=error
    with response:
        return response.status,dict(response.headers),response.read()
assert json.loads(get(base+'/__audit_identity')[2])['audit']=='animecore-fix-verification'
fixture=json.loads(next(s[7:] for s in Path(os.environ['AUDIT_TOKEN_FILE']).read_text(encoding='utf-8-sig').splitlines() if s.startswith('TOKENS=')))
headers={'Authorization':'Bearer '+fixture['tokens'][0]['access'],'Content-Type':'application/json'}
result={}
path=fixture['download'].split('?')[0]
status,_,body=get(base+path+'?episode=2&season=1&start=0&end=1.5&quality=720&format=mp4')
result['downloadAdmission']=status
if status!=202:raise RuntimeError(f'Download admission {status}: {body[:200]!r}')
job=json.loads(body);statuses=[]
for i in range(60):
    time.sleep(1);status,_,body=get(base+path+'?job_id='+job['job_id']);statuses.append(status)
    if status==200:break
    if status!=202:raise RuntimeError(f'Download worker {status}: {body[:200]!r}')
assert status==200
result['download']={'statuses':statuses,'bytes':len(body)}
status,_,body=get(base+'/api/anime/kodik/user-add/',headers,{'shikimori_ids':[1,2]})
result['importAdmission']=status
if status not in (200,202):raise RuntimeError(f'Import admission {status}: {body[:200]!r}')
progress=json.loads(body);token=progress['progress_token']
for i in range(60):
    if progress['status']=='ready':break
    time.sleep(1);status,_,body=get(base+'/api/anime/kodik/user-add/progress/?token='+token,headers);progress=json.loads(body)
    if status!=200 or progress['status']=='failed':raise RuntimeError(f'Import worker: {body[:200]!r}')
assert progress['status']=='ready' and progress['current']==2
result['import']={key:progress[key] for key in ('status','current','total')}
status,headers,body=get('http://127.0.0.1:4388'+fixture['download'],{'Range':'bytes=2-4'})
result['nginxRange']={'status':status,'contentRange':headers.get('Content-Range'),'body':body.decode()}
result['internalDirectStatus']=get('http://127.0.0.1:4388/_prepared_downloads/denied.mp4')[0]
assert status==206 and body==b'234' and result['internalDirectStatus']==404
Path(os.environ['AUDIT_RESULT_FILE']).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
