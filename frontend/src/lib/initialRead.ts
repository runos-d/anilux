import axios, { CanceledError, type InternalAxiosRequestConfig } from 'axios';

interface InitialRead {
  url: string;
  token: string;
  created: number;
  controller: AbortController;
  promise: Promise<{ data: unknown; status: number; headers: Record<string, string> } | null>;
}
declare global { interface Window { __initialReads?: InitialRead[] } }

export function cancelInitialReads(): void {
  window.__initialReads?.splice(0).forEach(read => read.controller.abort());
}

function canonical(url: string): string {
  const parsed = new URL(url, location.origin);
  parsed.searchParams.sort();
  return parsed.href;
}

export function useInitialRead(config: InternalAxiosRequestConfig): void {
  if (config.method !== 'get' || !window.__initialReads?.length) return;
  const token = localStorage.getItem('anilux_access_token_v1') || '';
  const url = canonical(axios.getUri(config));
  const index = window.__initialReads.findIndex(read => read.token === token &&
    Date.now() - read.created < 15000 && canonical(read.url) === url);
  if (index < 0) return;
  const read = window.__initialReads.splice(index, 1)[0]!;
  const fallback = axios.getAdapter(config.adapter);
  config.adapter = async current => {
    const abort = () => read.controller.abort();
    if (current.signal?.aborted) { abort(); throw new CanceledError(); }
    current.signal?.addEventListener?.('abort', abort, { once:true });
    try {
      const result = await read.promise;
      if (current.signal?.aborted || token !== (localStorage.getItem('anilux_access_token_v1') || ''))
        throw new CanceledError('Login session changed or request cancelled');
      return result ? { ...result, config:current, statusText:'OK' } : fallback(current);
    } finally { current.signal?.removeEventListener?.('abort', abort); }
  };
}
