import { QueryClient } from "@tanstack/vue-query";
import axios from 'axios';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 15 * 60_000,
      retry: (attempt, error) => attempt < 1 && axios.isAxiosError(error) && !axios.isCancel(error) &&
        (!error.response || error.response.status >= 500),
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30_000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
  },
});

const queryKeyText = (key: readonly unknown[]) => key
  .map(part => typeof part === 'string' ? part : JSON.stringify(part))
  .join(':')
  .toLowerCase();

export const invalidateQueryGroups = (groups: readonly string[]) => {
  if (!groups.length) return Promise.resolve();
  const normalized = groups.map(group => group.toLowerCase());
  return queryClient.invalidateQueries({
    predicate: query => {
      const key = queryKeyText(query.queryKey);
      return normalized.some(group => key.includes(group));
    },
  });
};
