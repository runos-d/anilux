import { beforeEach, expect, it, vi } from 'vitest';
import axios, { AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';
import { useInitialRead, cancelInitialReads } from './initialRead';

const fallback = vi.fn(async config => ({ data:'fresh', status:200, statusText:'OK', headers:{}, config }));
const config = (params = { sections:'a,b' }): InternalAxiosRequestConfig => ({
  method:'get', baseURL:location.origin+'/api', url:'/anime/home/personalized/',
  params, headers:new AxiosHeaders(), adapter:fallback,
});
function seed(promise = Promise.resolve({ data:'early', status:200, headers:{} })) {
  window.__initialReads = [{ url:'/api/anime/home/personalized/?sections=a,b', token:'owner', created:Date.now(),
    controller:new AbortController(), promise }];
}
beforeEach(() => { fallback.mockClear(); localStorage.setItem('anilux_access_token_v1','owner'); window.__initialReads = []; });

it('reuses exactly one matching read, including equivalent encoded parameters', async () => {
  seed(); const request = config(); useInitialRead(request);
  const response = await axios.getAdapter(request.adapter)(request);
  expect(response.data).toBe('early'); expect(fallback).not.toHaveBeenCalled();
  const second = config(); useInitialRead(second);
  expect(second.adapter).toBe(fallback);
});
it('does not reuse another session or different filters', () => {
  seed(); localStorage.setItem('anilux_access_token_v1','reader');
  const request = config(); useInitialRead(request); expect(request.adapter).toBe(fallback);
  localStorage.setItem('anilux_access_token_v1','owner');
  const filtered = config({ sections:'other' }); useInitialRead(filtered); expect(filtered.adapter).toBe(fallback);
});
it('falls back on failed early fetch and cancels a response after account switch', async () => {
  seed(Promise.resolve(null) as never); const request = config(); useInitialRead(request);
  expect((await axios.getAdapter(request.adapter)(request)).data).toBe('fresh');
  seed(); const changed = config(); useInitialRead(changed);
  localStorage.setItem('anilux_access_token_v1','reader');
  await expect(axios.getAdapter(changed.adapter)(changed)).rejects.toSatisfy(axios.isCancel);
});
it('clears and aborts unconsumed reads when the account changes', () => {
  seed(); const controller = window.__initialReads![0]!.controller;
  cancelInitialReads(); expect(controller.signal.aborted).toBe(true); expect(window.__initialReads).toEqual([]);
});
