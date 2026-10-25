import apiClient from './client';

export interface Excerpt {
  id: number;
  anime_id: number;
  anime_title: string;
  poster_url?: string | null;
  season: number;
  episode: number;
  translation_id: number;
  translation_title: string;
  player_link: string;
  duration: number;
  start: number;
  end: number;
  title: string;
  description: string;
  shared: boolean;
  share_path?: string | null;
  unavailable?: boolean;
}
export type ExcerptEdit = Pick<Excerpt, 'start' | 'end' | 'title' | 'description'>;
export type ExcerptCreate = ExcerptEdit & Pick<Excerpt, 'anime_id' | 'season' | 'episode' | 'translation_id' | 'duration'>;
export const excerptsApi = {
  list: (q = '', page = 1) => apiClient.get<{ results: Excerpt[]; count: number; next: number | null }>('/anime/excerpts/', { params: { q, page } }),
  get: (id: number) => apiClient.get<Excerpt>(`/anime/excerpts/${id}/`),
  shared: (token: string) => apiClient.get<Excerpt>(`/anime/excerpts/shared/${token}/`),
  create: (data: ExcerptCreate) => apiClient.post<Excerpt>('/anime/excerpts/', data),
  update: (id: number, data: Partial<ExcerptEdit> & { shared?: boolean }) => apiClient.patch<Excerpt>(`/anime/excerpts/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/anime/excerpts/${id}/`),
};
export function excerptTime(time: number): string {
  const hundredths = Math.round(time * 100), seconds = Math.floor(hundredths / 100), fraction = hundredths % 100;
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}${fraction ? '.' + String(fraction).padStart(2, '0') : ''}`;
}
export function parseExcerptTime(value: string): number {
  if (!/^\d+(?:\.\d+)?$|^\d+:\d{1,2}(?:\.\d+)?$|^\d+:\d{1,2}:\d{1,2}(?:\.\d+)?$/.test(value.trim())) return NaN;
  const parts = value.trim().split(':').map(Number);
  if (parts.slice(1).some(part => part >= 60)) return NaN;
  return parts.reduce((total, part) => total * 60 + part, 0);
}
export function excerptError(error: unknown): string {
  const data = (error as { response?: { data?: Record<string, unknown> } })?.response?.data;
  return data ? Object.values(data).flat().join(' ') : 'Не удалось выполнить действие. Попробуйте ещё раз.';
}
