// Node 22+, run from repository root. Tokens and all writes belong to the disposable schema.
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { monitorEventLoopDelay, performance } from 'node:perf_hooks';
const require = createRequire(new URL('../../../frontend/package.json', import.meta.url));
const WebSocket = require('ws');
const base = 'http://127.0.0.1:4386';
const target = Math.min(6000, Number(process.env.CAPACITY_USERS || 6000));
const input = readFileSync(process.env.CAPACITY_TOKEN_FILE, 'utf8').split(/\r?\n/).find(x => x.startsWith('TOKENS='));
const fixture = JSON.parse(input.slice(7));
const users = fixture.users.slice(0, target);
if (users.length !== target) throw Error('Insufficient disposable users');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const read = async url => {
  const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  return response.json();
};
// Check every process, not merely the first answer returned by the balancer.
for (let port=4387; port<=4390; port++) {
  const status = await read(`http://127.0.0.1:${port}/__capacity_identity`);
  if (status.identity !== 'animecore-capacity-isolated') throw Error('Refusing non-isolated target');
}
if ((await read(`${base}/__capacity_identity`)).identity !== 'animecore-capacity-isolated') throw Error('Wrong gateway');
const check = await fetch(`${base}/api/users/profile/`, { headers: { Authorization: `Bearer ${users[0].access}` } });
if (check.status !== 200) throw Error(`Fixture authentication failed (${check.status})`);
await check.arrayBuffer();
const metrics = async () => Promise.all([4387,4388,4389,4390].map(port => read(`http://127.0.0.1:${port}/__capacity_metrics`).catch(() => ({unavailable:true}))));
const percentile = (values,p) => values.length ? [...values].sort((a,b)=>a-b)[Math.min(values.length-1, Math.floor(values.length*p))] : null;
const stats = values => ({ count: values.length, p50_ms: percentile(values,.5), p95_ms: percentile(values,.95), max_ms: values.length ? values.reduce((a,b)=>Math.max(a,b),0) : null });
const result = { target_users: target, transport:'subprotocol', unique_recipient_checks:true, ramp_batch:Number(process.env.CAPACITY_RAMP_BATCH||16), fixture: { rooms:fixture.rooms,room_size:fixture.room_size||60,posts:fixture.posts,anime:fixture.anime }, limits: { api_processes:4,cpu_each:1,memory_each_mib:1024 }, stages:[], generator:{} };
const sockets = [], pairs = [];
const outstanding = new Map();
const delay = monitorEventLoopDelay({ resolution:20 });delay.enable();
let closing=false, opens=0, init=0, failures=0, closes=0, frameErrors=0, deliveries=0, activeStage=null;
const connectionErrors={},closeCodes={};
const connectionLatency=[], initialLatency=[], ackLatency=[], deliveryLatency=[];
function socket(user, kind) {
  const openedAt=performance.now();
  return new Promise(resolve => {
    let settled=false;
    const path=kind==='global' ? '/ws/global/' : `/ws/chat/${user.chat_id}/?type=group`;
    const ws=new WebSocket(`${base.replace('http','ws')}${path}`,['animecore.v2',`auth.${user.access}`]);
    sockets.push(ws);ws.nextPing=performance.now()+1000+Math.random()*24000;
    const timer=setTimeout(()=>{ if(!settled){failures++;settled=true;ws.terminate();resolve(null);}},30000);
    const done=value=>{if(!settled){settled=true;clearTimeout(timer);resolve(value);}};
    ws.on('open',()=>{opens++;connectionLatency.push(performance.now()-openedAt);if(kind==='global')done(ws);});
    ws.on('message',raw=>{
      let data;try{data=JSON.parse(raw);}catch{frameErrors++;return;}
      if(data.action==='init'){init++;initialLatency.push(performance.now()-openedAt);done(ws);}
      const key=data.message?.client_message_id;
      const command=key&&outstanding.get(key);
      if(data.action==='message_ack'&&command&&!command.acked){command.acked=true;if(command.stage.closed){command.stage.late_acks=(command.stage.late_acks||0)+1;return;}const ms=performance.now()-command.start;ackLatency.push(ms);command.stage.acks.push(ms);}
      if(data.action==='new_message'&&command){
        if(command.stage.closed){command.stage.late_deliveries=(command.stage.late_deliveries||0)+1;return;}
        if(String(data.chat_id)!==String(user.chat_id)||String(command.room)!==String(user.chat_id)){command.stage.unexpected_recipients++;return;}
        const recipient=`${user.user_id}:${kind}`;
        if(!command.received.has(recipient)){command.received.add(recipient);deliveries++;const ms=performance.now()-command.start;deliveryLatency.push(ms);command.stage.deliveries++;command.stage.deliveryTimes.push(ms);}
      }
      if(data.action==='error'){frameErrors++;if(activeStage)activeStage.chat_errors++;}
    });
    ws.on('error',error=>{if(!settled){failures++;const message=String(error.message).replace(/token=[^\s]+/g,'token=REDACTED').slice(0,120);connectionErrors[message]=(connectionErrors[message]||0)+1;}done(null);});
    ws.on('close',code=>{if(!closing){closes++;closeCodes[code]=(closeCodes[code]||0)+1;}done(null);});
  });
}
const heartbeat=setInterval(()=>{
  const now=performance.now();
  for(const ws of sockets)if(ws.readyState===WebSocket.OPEN&&now>=ws.nextPing){ws.nextPing=now+25000;ws.send(JSON.stringify({action:'ping',is_active:true}));}
},250);
const started=performance.now();
process.on('SIGINT',()=>{closing=true;clearInterval(heartbeat);for(const ws of sockets)ws.terminate();process.exit(130);});
try {
  const batchSize=Number(process.env.CAPACITY_RAMP_BATCH||16);
  for(let offset=0;offset<users.length;offset+=batchSize){
    const batch=users.slice(offset,offset+batchSize);
    const connected=await Promise.all(batch.map(async user=>{const [global,chat]=await Promise.all([socket(user,'global'),socket(user,'chat')]);return {user,global,chat};}));
    pairs.push(...connected);
    if(offset%256===0)console.log(JSON.stringify({ramp_users:pairs.length,opens,init,failures,closes}));
    if(failures>Math.max(5,pairs.length*.02)||closes>Math.max(10,pairs.length*.02)){result.stop_reason='Connection ramp exceeded 2% failures/closures';break;}
    await sleep(200);
  }
  result.ramp_seconds=(performance.now()-started)/1000;
  await sleep(3000);
  result.connections={users:pairs.length,opens,initialized_chat:init,currently_open:sockets.filter(s=>s.readyState===WebSocket.OPEN).length,failures,closes,handshake:stats(connectionLatency),snapshot:stats(initialLatency),nodes:await metrics()};
  console.log(JSON.stringify({connections:result.connections}));
  // Offered load: reads plus durable sends, two recipient sockets per user.
  const plans=JSON.parse(process.env.CAPACITY_STAGES||'[[30,2,20],[100,5,20],[300,10,20],[600,30,20],[1200,100,30]]');
  let requestIndex=0, chatIndex=0;
  for(const [httpRate,chatRate,seconds] of plans){
    if(result.stop_reason)break;
    const stage={http_rps:httpRate,chat_messages_per_second:chatRate,seconds,http_sent:0,http_errors:0,statuses:{},latencies:[],chat_sent:0,chat_errors:0,acks:[],deliveries:0,expected_deliveries:0,unexpected_recipients:0,deliveryTimes:[]};activeStage=stage;
    const roomSockets=new Map();for(const pair of pairs){const key=String(pair.user.chat_id);roomSockets.set(key,(roomSockets.get(key)||0)+Number(pair.global?.readyState===WebSocket.OPEN)+Number(pair.chat?.readyState===WebSocket.OPEN));}
    const stageStart=performance.now();const pending=new Set();let nextHttp=0,nextChat=0;
    const request=async index=>{
      const user=users[index%users.length];
      const paths=['/api/anime/?page_size=20','/api/social/feed/?page_size=20&include_count=false','/api/anime/?search=Capacity&page_size=20','/api/social/feed/weighted/?page_size=20&include_count=false'];
      const begin=performance.now();stage.http_sent++;
      try{const response=await fetch(base+paths[index%paths.length],{headers:{Authorization:`Bearer ${user.access}`},signal:AbortSignal.timeout(8000)});await response.arrayBuffer();stage.statuses[response.status]=(stage.statuses[response.status]||0)+1;if(!response.ok)stage.http_errors++;}
      catch{stage.http_errors++;stage.statuses.network=(stage.statuses.network||0)+1;}
      stage.latencies.push(performance.now()-begin);
    };
    while(performance.now()-stageStart<seconds*1000){
      const elapsed=(performance.now()-stageStart)/1000;
      while(nextHttp<elapsed*httpRate){nextHttp++;const p=request(requestIndex++);pending.add(p);p.finally(()=>pending.delete(p));}
      while(nextChat<elapsed*chatRate){nextChat++;const pair=pairs[chatIndex++%pairs.length];if(pair.chat?.readyState!==WebSocket.OPEN){stage.chat_errors++;continue;}const id=randomUUID();outstanding.set(id,{start:performance.now(),stage,acked:false,received:new Set(),room:pair.user.chat_id});stage.chat_sent++;stage.expected_deliveries+=roomSockets.get(String(pair.user.chat_id))||0;pair.chat.send(JSON.stringify({action:'send_message',text:`Capacity ${id}`,client_message_id:id}));}
      if(pending.size>httpRate*8+100){stage.overload=true;break;}
      await sleep(20);
    }
    await Promise.allSettled(pending);await sleep(5000);
    stage.closed=true;stage.http=stats(stage.latencies);stage.ack=stats(stage.acks);stage.delivery=stats(stage.deliveryTimes);delete stage.latencies;delete stage.acks;delete stage.deliveryTimes;
    stage.nodes=await metrics();stage.open_sockets=sockets.filter(s=>s.readyState===WebSocket.OPEN).length;
    result.stages.push(stage);activeStage=null;console.log(JSON.stringify({stage}));
    if(stage.http_errors/Math.max(1,stage.http_sent)>.01||stage.http.p95_ms>1000||stage.ack.count<stage.chat_sent*.99||stage.delivery.p95_ms>1000||stage.deliveries<stage.expected_deliveries*.99||stage.unexpected_recipients){result.stop_reason='Stage exceeded SLO: errors 1%, p95 1 second, or missing ACK/recipient delivery';break;}
    outstanding.clear();
  }
} catch(error){result.error=String(error.message).replace(/token=[^\s]+/g,'token=REDACTED');}
finally {
  result.final={opens,init,failures,closes,connectionErrors,closeCodes,frameErrors,deliveries,open_sockets:sockets.filter(s=>s.readyState===WebSocket.OPEN).length,nodes:await metrics()};
  result.generator={event_loop_p95_ms:delay.percentile(95)/1e6,event_loop_max_ms:delay.max/1e6,rss_mib:process.memoryUsage().rss/1024/1024};
  closing=true;clearInterval(heartbeat);delay.disable();for(const ws of sockets)ws.terminate();
  writeFileSync(new URL('./mixed-load.json',import.meta.url),JSON.stringify(result,null,2));console.log(JSON.stringify({saved:'mixed-load.json',stop_reason:result.stop_reason,error:result.error,generator:result.generator}));
}
