import apiClient from '@/api/client';
import { postAccountGuard } from './postAccount';
import { postDraftGet, postDraftPut } from './postDrafts';

export const POST_MAX_BYTES = 250 * 1024 * 1024;
export const POST_CHUNK_BYTES = 4 * 1024 * 1024;

export function validatePostFiles(files: File[], retainedBytes = 0): void {
  if (retainedBytes + files.reduce((sum, file) => sum + file.size, 0) > POST_MAX_BYTES)
    throw new Error('Общий объём вложений поста -максимум 250 МБ');
  if (files.some(file => !/\.(jpe?g|png|webp|gif|mp4|webm|mov|mkv|avi|m4v)$/i.test(file.name)))
    throw new Error('Неподдерживаемый формат изображения или видео');
}

interface Upload { id: string; offset: number; size: number; state: string; }
async function checksum(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

const fingerprints = new WeakMap<File, Promise<string>>();
export function fileIdentity(owner: string | number, file: File, index: number): Promise<string> {
  let fingerprint = fingerprints.get(file);
  if (!fingerprint) { fingerprint = checksum(file); fingerprints.set(file, fingerprint); }
  return fingerprint.then(hash => `${owner}:${hash}:${file.name}:${index}`);
}

export async function uploadPostFiles(owner: number | string, files: File[], progress: (percent: number) => void): Promise<string[]> {
  validatePostFiles(files);
  const ensureAccount = postAccountGuard(owner);
  ensureAccount();
  const offsets = files.map(() => 0);
  const inFlight = files.map(() => 0);
  const total = files.reduce((sum, file) => sum + file.size, 0);
  const ids: string[] = new Array(files.length);
  let next = 0;
  const reportProgress = () => progress(Math.round(offsets.reduce((sum, offset, index) => sum + offset + inFlight[index]!, 0) / Math.max(1, total) * 100));
  async function send(index: number) {
    const file = files[index]!;
    const identity = await fileIdentity(owner, file, index);
    ensureAccount();
    const saved = await postDraftGet<Upload>('uploads', identity).catch(() => undefined);
    let upload: Upload | undefined;
    if (saved) {
      try { upload = (await apiClient.get<Upload>(`/social/post-uploads/${saved.id}/`, { _accountId: String(owner), _keepOnNavigation: true })).data; }
      catch { /* An expired session is restarted from the local draft. */ }
      if (upload && !['uploading', 'uploaded'].includes(upload.state)) upload = undefined;
    }
    ensureAccount();
    if (!upload) upload = (await apiClient.post<Upload>('/social/post-uploads/', { filename: file.name, size: file.size }, { _accountId: String(owner) })).data;
    ensureAccount();
    await postDraftPut('uploads', identity, upload).catch(() => undefined);
    offsets[index] = upload.offset;
    reportProgress();
    while (upload.offset < file.size) {
      ensureAccount();
      const chunk = file.slice(upload.offset, upload.offset + POST_CHUNK_BYTES);
      let response: Upload | undefined;
      const hash = await checksum(chunk);
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          ensureAccount();
          response = (await apiClient.patch<Upload>(`/social/post-uploads/${upload.id}/`, chunk, {
            _accountId: String(owner),
            headers: { 'Content-Type': 'application/octet-stream', 'Upload-Offset': String(upload.offset), 'Upload-Checksum': hash },
            timeout: 60_000,
            onUploadProgress: event => {
              inFlight[index] = Math.min(chunk.size, event.loaded);
              reportProgress();
            },
          })).data;
          break;
        } catch (error) {
          const failure = error as { response?: { status: number; data: Upload } };
          if (failure.response?.status === 409) { response = failure.response.data; break; }
          if (attempt === 2 || failure.response && failure.response.status < 500) throw error;
        }
      }
      if (!response || response.offset <= upload.offset) throw new Error('Не удалось продолжить загрузку файла');
      ensureAccount();
      upload = response;
      offsets[index] = upload.offset;
      inFlight[index] = 0;
      reportProgress();
    }
    ensureAccount();
    upload = (await apiClient.post<Upload>(`/social/post-uploads/${upload.id}/complete/`, undefined, { _accountId: String(owner) })).data;
    ids[index] = upload.id;
    ensureAccount();
    await postDraftPut('uploads', identity, upload).catch(() => undefined);
  }
  async function worker() {
    while (next < files.length) { const index = next++; await send(index); }
  }
  await Promise.all([worker(), worker()]);
  return ids;
}

export async function forgetPostUploads(owner: number | string, files: File[]) {
  await Promise.all(files.map(async (file, index) => postDraftPut('uploads',
    await fileIdentity(owner, file, index)).catch(() => undefined)));
}
