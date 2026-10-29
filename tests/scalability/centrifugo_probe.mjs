// Official JS SDK; synthetic transport only. Never accepts an external target.
import { Centrifuge } from 'centrifuge';
import WebSocket from 'ws';
import { createHmac, randomUUID } from 'node:crypto';
import { monitorEventLoopDelay, performance } from 'node:perf_hooks';

const count = Number(process.env.PROBE_CLIENTS || 60);
if (!Number.isInteger(count) || count < 1 || count > 500) throw Error('Client budget is 1..500');
const channel = `lab:probe-${randomUUID()}`;
const encode = value => Buffer.from(JSON.stringify(value)).toString('base64url');
const token = sub => {
  const value = `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode({ sub, exp: Math.floor(Date.now()/1000)+120 })}`;
  return `${value}.${createHmac('sha256','disposable-lab-centrifugo-not-production').update(value).digest('base64url')}`;
};
const clients = [], received = new Set(), latencies = [], sentAt = new Map();
const scheduler = monitorEventLoopDelay({ resolution: 10 });
scheduler.enable();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const percentile = (values, p) => [...values].sort((a,b)=>a-b)[Math.ceil(values.length*p)-1] ?? null;
let duplicate = 0, unexpected = 0, errors = 0, deniedChannel = false, deniedPublish = false;
try {
  // Health and API remain inside the lab network. API key is synthetic.
  const health = await fetch('http://centrifugo:9000/health', { signal: AbortSignal.timeout(5000) });
  if (!health.ok) throw Error('Lab transport not ready');
  for (let i=0;i<count;i++) {
    const client = new Centrifuge('ws://centrifugo:8000/connection/websocket', {
      token: token(`synthetic-${i}`), websocket: WebSocket,
      maxReconnectDelay: 2000, minReconnectDelay: 500, timeout: 5000,
    });
    clients.push(client);
    const subscription = client.newSubscription(channel);
    subscription.on('publication', context => {
      const start = sentAt.get(context.data.sequence);
      if (start === undefined) { unexpected++; return; }
      const key = `${i}:${context.data.sequence}`;
      if (received.has(key)) { duplicate++; return; }
      received.add(key);
      latencies.push(performance.now() - start);
    });
    client.on('error', () => { errors++; });
    client.connect(); subscription.subscribe();
    await subscription.ready(10000);
  }
  try { const sub = clients[0].newSubscription('conversation:1'); sub.subscribe(); await sub.ready(1500); }
  catch { deniedChannel = true; }
  try { await clients[0].publish(channel, { forbidden: true }); }
  catch { deniedPublish = true; }
  for (let sequence=0;sequence<20;sequence++) {
    sentAt.set(sequence, performance.now());
    const response = await fetch('http://centrifugo:9000/api/publish', {
      method: 'POST', headers: {'Content-Type':'application/json','X-API-Key':'disposable-lab-api-only'},
      body: JSON.stringify({channel,data:{sequence,text:'x'.repeat(128)}}), signal:AbortSignal.timeout(5000),
    });
    const body = await response.json();
    if (!response.ok || body.error) throw Error('Synthetic publish failed');
    await wait(100);
  }
  const deadline = performance.now()+5000;
  while (received.size<count*20 && performance.now()<deadline) await wait(25);
  const passed = received.size===count*20 && !unexpected && !duplicate && deniedChannel && deniedPublish;
  console.log(JSON.stringify({
    schema_version:1, transport:'centrifugo-6.10.2', sdk:'centrifuge-5.8.0',
    synthetic_only:true, capacity_certified:false, security_equivalence:false,
    active_session_check_per_delivery:'not_implemented_in_this_prototype',
    clients:count, publications:20, expected_deliveries:count*20, unique_deliveries:received.size,
    duplicate, unexpected, client_errors:errors, denied_unknown_namespace:deniedChannel,
    denied_client_publish:deniedPublish, delivery_ms:{p95:percentile(latencies,.95),p99:percentile(latencies,.99)},
    generator:{rss_bytes:process.memoryUsage().rss,event_loop_p99_ms:scheduler.percentile(99)/1e6},
    passed_transport_smoke:passed,
  },null,2));
  if (!passed) process.exitCode=2;
} finally { scheduler.disable(); for (const client of clients) client.disconnect(); }
