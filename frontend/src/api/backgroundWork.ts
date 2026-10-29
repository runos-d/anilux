import { CanceledError, isCancel } from 'axios';
import type { AxiosRequestConfig } from 'axios';
import apiClient from './client';

function scope() {
  let id: number | undefined;
  try { id = JSON.parse(localStorage.getItem('anilux_user_v1') || 'null')?.id; } catch {}
  return `${location.pathname}:${id || 'guest'}:${!!localStorage.getItem('anilux_access_token_v1')}`;
}
const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function preparedDownload(url: string, config: AxiosRequestConfig) {
  const owner = scope();
  let jobId: string | undefined;
  for (let attempt = 0; attempt < 150; attempt++) {
    if (scope() !== owner || config.signal?.aborted) throw new CanceledError('Download screen closed');
    try {
      const response = await apiClient.get<Blob>(url, {
        ...config, params: jobId ? { job_id: jobId } : config.params,
        responseType: 'blob', timeout: 20_000,
        onDownloadProgress: event => {
          const xhr = event.event?.target as XMLHttpRequest | undefined;
          if (xhr?.status !== 202) config.onDownloadProgress?.(event);
        },
      });
      if (response.status !== 202) return response;
      const data = JSON.parse(await response.data.text()) as { job_id: string; retry_after?: number };
      jobId = data.job_id;
      await wait(Math.max(1, Math.min(data.retry_after || 2, 5)) * 1000);
    } catch (error) {
      if (isCancel(error)) throw error;
      const blob = (error as { response?: { data?: unknown } }).response?.data;
      if (blob instanceof Blob) {
        const data = await blob.text().then(text => JSON.parse(text)).catch(() => ({}));
        throw new Error(data.error || data.detail || 'Не удалось подготовить файл');
      }
      throw error;
    }
  }
  throw new Error('Подготовка ещё не завершена. Повторите запрос позже.');
}

export async function importCatalog(data: object, progress: (data: { current: number; total: number; percent: number; current_title: string }) => void) {
  const owner = scope();
  let response = await apiClient.post('/anime/kodik/user-add/', data);
  if (response.status !== 202) return response;
  const token = response.data.progress_token as string;
  for (let attempt = 0; attempt < 600; attempt++) {
    if (scope() !== owner) throw new CanceledError('Import screen closed');
    await wait(2000);
    if (scope() !== owner) throw new CanceledError('Import screen closed');
    response = await apiClient.get('/anime/kodik/user-add/progress/', { params: { token } });
    progress({ current: response.data.current, total: response.data.total, percent: response.data.percent, current_title: 'Подготовка тайтлов' });
    if (response.data.status === 'failed') throw new Error(response.data.error || 'Не удалось импортировать тайтлы');
    if (response.data.status === 'ready') return response;
  }
  throw new Error('Импорт ещё не завершён. Повторите проверку позже.');
}
