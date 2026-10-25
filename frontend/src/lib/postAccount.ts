import { useAuthStore } from '@/stores/auth';
import { usePostStore } from '@/stores/posts';

/** Stop a task permanently when its originating login session is replaced. */
export function postAccountGuard(owner: string | number): () => void {
  const auth = useAuthStore();
  const posts = usePostStore();
  const generation = posts.sessionGeneration;
  return () => {
    if (String(auth.user?.id) !== String(owner) || generation !== posts.sessionGeneration) {
      const error = new Error('Отправка остановлена: аккаунт изменился');
      error.name = 'AbortError';
      throw error;
    }
  };
}
