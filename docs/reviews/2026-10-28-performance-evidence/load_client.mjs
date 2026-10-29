import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../../../frontend/package.json', import.meta.url));
const WebSocket = require('ws');
const base = 'http://127.0.0.1:4387';
if ((await fetch(base + '/__audit_identity').then(r => r.json())).audit !== 'animecore-fix-verification') throw Error('Wrong server');
const line = fs.readFileSync(process.env.AUDIT_TOKEN_FILE, 'utf8').split(/\r?\n/).find(row => row.startsWith('TOKENS='));
const fixture = JSON.parse(line.slice(7));
if (JSON.parse(Buffer.from(fixture.tokens[0].access.split('.')[1], 'base64url')).exp * 1000 - Date.now() < 120000) throw Error('Fixture token expired; regenerate fixtures');
if ((await fetch(base+'/api/users/profile/', { headers:{Authorization:'Bearer '+fixture.tokens[0].access} })).status !== 200) throw Error('Fixture authentication failed');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const percentile = (rows, p) => [...rows].sort((a, b) => a - b)[Math.min(rows.length - 1, Math.ceil(rows.length * p) - 1)] || 0;
const result = { environment: { appCpuLimit: 2, mysqlCpuLimit: 2, users: 100, anime: 10000 }, phases: [] };
async function phase(name, path, rate, seconds, authenticated = false) {
  const pending = [], times = [], statuses = {};
  const start = performance.now();
  for (let i = 0; i < rate * seconds; i++) {
    await delay(Math.max(0, start + i * 1000 / rate - performance.now()));
    pending.push((async () => {
      const begin = performance.now();
      try {
        const response = await fetch(base + (typeof path === 'function' ? path(i) : path), {
          headers: authenticated ? { Authorization: 'Bearer ' + fixture.tokens[i % fixture.tokens.length].access } : {},
          signal: AbortSignal.timeout(10000),
        });
        await response.arrayBuffer();
        statuses[response.status] = (statuses[response.status] || 0) + 1;
      } catch { statuses.networkError = (statuses.networkError || 0) + 1; }
      times.push(performance.now() - begin);
    })());
  }
  await Promise.all(pending);
  const elapsed = (performance.now() - start) / 1000;
  const row = { name, requests: times.length, elapsedSeconds: elapsed, requestsPerSecond: times.length / elapsed,
    p50Ms: percentile(times, .5), p95Ms: percentile(times, .95), p99Ms: percentile(times, .99), statuses };
  result.phases.push(row); console.log(JSON.stringify(row));
}
await fetch(base + '/api/anime/?page_size=20');
await phase('cached guest catalog', '/api/anime/?page_size=20', 25, 15);
await phase('cached authenticated catalog 25rps', '/api/anime/?page_size=20', 25, 10, true);
await phase('cached authenticated catalog 50rps', '/api/anime/?page_size=20', 50, 10, true);
await phase('cached authenticated catalog 100rps', '/api/anime/?page_size=20', 100, 10, true);
await phase('authenticated contact-only user search', '/api/users/search/?search=probe', 20, 10, true);
await phase('uncached catalog keys', i => '/api/anime/?page_size=20&audit=' + i, 5, 5);

const socketErrors = [];
const sockets = [], received = Array.from({ length: 100 }, () => []);
const started = performance.now();
await Promise.all(fixture.tokens.map((row, index) => new Promise((resolve, reject) => {
  const socket = new WebSocket('ws://127.0.0.1:4387/ws/global/?token=' + encodeURIComponent(row.access));
  sockets.push(socket);
  const timeout = setTimeout(() => reject(Error('WS open timeout')), 15000);
  socket.once('open', () => { clearTimeout(timeout); resolve(); });
  socket.on('error', error => { socketErrors.push(error.message); reject(error); });
  socket.on('message', raw => {
    const value = JSON.parse(raw);
    if (value.action === 'ping') socket.send(JSON.stringify({ action: 'pong' }));
    if (value.action === 'audit_probe') received[index].push(value.data.sequence);
  });
})));
await delay(1000);
await delay(6000);
const before = await fetch(base + '/__audit_metrics').then(r => r.json());
for (let sequence = 0; sequence < 30; sequence++) await fetch(base + '/__audit_event', {
  method: 'POST', body: JSON.stringify({ target: fixture.tokens[0].user_id, sequence }),
});
for (let i = 0; i < 100 && received[0].length < 30; i++) await delay(100);
const after = await fetch(base + '/__audit_metrics').then(r => r.json());
result.websockets = { opened: sockets.length, openAndDeliveryMs: performance.now() - started,
  socketErrors, stillOpen: sockets.filter(socket=>socket.readyState===WebSocket.OPEN).length, targetReceived: received[0].length, otherReceived: received.slice(1).reduce((sum, row) => sum + row.length, 0),
  sessionValidationDelta: after.session_validations - before.session_validations };
result.resources = after;
for (const socket of sockets) socket.close();
const range = await fetch(base + fixture.download, { headers: { Range: 'bytes=2-4' } });
result.asyncRange = { status: range.status, contentRange: range.headers.get('content-range'), body: await range.text() };
fs.writeFileSync(process.env.AUDIT_RESULT_FILE, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ websockets: result.websockets, resources: result.resources, asyncRange: result.asyncRange }));
await delay(1000);
