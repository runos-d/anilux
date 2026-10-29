import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../../../frontend/package.json', import.meta.url));
const WebSocket = require('ws');
const base = 'http://127.0.0.1:4388';
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
await phase('four HTTP replicas, authenticated cached catalog 100rps', '/api/anime/?page_size=20', 100, 20, true);
result.environment.appReplicas = 4;
fs.writeFileSync(process.env.AUDIT_RESULT_FILE, JSON.stringify(result, null, 2));

