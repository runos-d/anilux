import { expect, it } from 'vitest';
import { developmentProxyTarget, resolveApiBase } from './localApi';
it.each(['http://localhost:8000/api','http://127.0.0.1:8000/api/','http://[::1]:8000/api'])('keeps local development API on the frontend origin: %s', url => {
  expect(resolveApiBase(url,'http://localhost:5173',true)).toBe('http://localhost:5173/api');
  expect(developmentProxyTarget(url)).toBe('http://127.0.0.1:8000');
});
it('preserves production and explicitly remote API settings', () => {
  expect(resolveApiBase('http://localhost:8000/api','https://site.test',false)).toBe('http://localhost:8000/api');
  expect(resolveApiBase('https://api.example.test/api','http://localhost:5173',true)).toBe('https://api.example.test/api');
  expect(developmentProxyTarget('https://api.example.test/api')).toBe('https://api.example.test');
});
it('uses the same origin without a configured API', () => {
  expect(resolveApiBase(undefined,'http://localhost:5173',true)).toBe('http://localhost:5173/api');
});
