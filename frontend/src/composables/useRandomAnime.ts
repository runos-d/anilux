import { ref } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '@/api/client';
import { useToast } from '@/composables/useToast';

export function useRandomAnime() {
  const loading = ref(false);
  const router = useRouter();
  const toast = useToast();
  const openRandom = async () => {
    if (loading.value) return;
    loading.value = true;
    try {
      const { data } = await apiClient.get('/anime/random/', { params: { t: Date.now() } });
      if (!data?.id) throw new Error('Empty random result');
      await router.push(`/anime/${data.slug || data.id}`);
    } catch { toast.error('Не удалось выбрать аниме. Попробуйте ещё раз.'); }
    finally { loading.value = false; }
  };
  return { loading, openRandom };
}
