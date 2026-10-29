import axios, { type AxiosInstance, type AxiosRequestConfig, CanceledError } from "axios";
import { isCancelledError as isQueryCancelled } from '@tanstack/vue-query';
import { useInitialRead } from '@/lib/initialRead';
import { resolveApiBase } from '@/lib/localApi';

declare module 'axios' { interface AxiosRequestConfig { _keepOnNavigation?: boolean; _accountId?: string; _sessionRefresh?: string | null; } }

interface AbortControllerRequestConfig extends AxiosRequestConfig {
  _abortController?: AbortController;
  _abortCleanup?: () => void;
  _callerSignal?: AxiosRequestConfig["signal"];
}
let baseURL = resolveApiBase(import.meta.env.VITE_API_URL, window.location.origin, import.meta.env.DEV);

baseURL = baseURL.replace(/\/api\/api$/, "/api").replace(/\/\/$/, "/").replace(/^https:\/\/localhost/, "http://localhost");

const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    Accept: "application/json",
  },
  timeout: 20_000,
  withCredentials: true,
});

const activeControllers = new Set<AbortController>();
const backgroundControllers = new Set<AbortController>();

apiClient.interceptors.request.use((config) => {
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) config.timeout = 300_000;
  const controller = new AbortController();
  (config as AbortControllerRequestConfig)._abortController = controller;
  const callerSignal = (config as AbortControllerRequestConfig)._callerSignal || config.signal;
  (config as AbortControllerRequestConfig)._callerSignal = callerSignal;
  if (callerSignal?.aborted) controller.abort();
  else if (callerSignal) {
    const abort = () => controller.abort();
    callerSignal.addEventListener?.('abort', abort, { once: true });
    (config as AbortControllerRequestConfig)._abortCleanup = () => callerSignal.removeEventListener?.('abort', abort);
  }
  config.signal = controller.signal;
  if (!config._keepOnNavigation && (!/\/social\/(post-uploads\/|posts\/)/.test(config.url || '') || config.method === 'get'))
    activeControllers.add(controller);
  else backgroundControllers.add(controller);
  useInitialRead(config);
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    if (['/users/change-password/', '/users/sessions/terminate/', '/users/sessions/terminate-all/'].includes(response.config.url || '') &&
        response.data?.tokens && response.config._sessionRefresh === localStorage.getItem('anilux_refresh_token_v1')) {
      localStorage.setItem('anilux_access_token_v1', response.data.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1', response.data.tokens.refresh);
    }
    const controller = (response.config as AbortControllerRequestConfig | undefined)?._abortController;
    if (controller) {
      activeControllers.delete(controller);
      backgroundControllers.delete(controller);
    }
    (response.config as AbortControllerRequestConfig)?._abortCleanup?.();
    return response;
  },
  (error) => {
    const controller = (error.config as AbortControllerRequestConfig | undefined)?._abortController;
    if (controller) {
      activeControllers.delete(controller);
      backgroundControllers.delete(controller);
    }
    (error.config as AbortControllerRequestConfig | undefined)?._abortCleanup?.();
    return Promise.reject(error);
  },
);

export const cancelAllRequests = (includeBackground = false) => {
  activeControllers.forEach((controller) => controller.abort());
  activeControllers.clear();
  if (includeBackground) {
    backgroundControllers.forEach(controller => controller.abort());
    backgroundControllers.clear();
  }
};

export const isRequestCancelled = (error: unknown): boolean =>
  isQueryCancelled(error) || (error instanceof Error &&
  (error.name === "CanceledError" || error.name === "AbortError"));

export const getMediaBaseUrl = () => {
  return baseURL.replace(/\/api$/, "");
};

export const getBackendOrigin = () => {
  return baseURL.replace(/\/api$/, "");
};

export const getMediaUrl = (
  path: string | null | undefined,
): string | undefined => {
  if (typeof path !== "string" || !path) return undefined;

  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("blob:") || path.startsWith("data:")) {
    return path;
  }

  if (import.meta.env.DEV && path.startsWith("/media/")) {
    return path;
  }

  const rawBase = import.meta.env.VITE_BASE_URL || getMediaBaseUrl();
  const baseUrl = String(rawBase).replace(/\/$/, "");
  return `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;
};

export const getWebpUrl = (url: string | undefined): string | undefined => {
  if (!url) return undefined;

  if (url.endsWith(".webp")) return url;

  if (
    url.includes("/media/") &&
    (url.endsWith(".png") || url.endsWith(".jpg") || url.endsWith(".jpeg"))
  ) {
    return url.replace(/\.(png|jpg|jpeg)(\?.*)?$/i, ".webp$2");
  }

  return url;
};

let refreshPromise: Promise<string> | null = null;

export const getRefreshedAccessToken = async (): Promise<string> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = localStorage.getItem("anilux_refresh_token_v1");
  if (!refreshToken) {
    throw new Error("No refresh token");
  }

  refreshPromise = (async () => {
    try {
      const response = await apiClient.post<{ access: string; refresh?: string }>(
        "/users/token/refresh/",
        { refresh: refreshToken },
      );
      if (localStorage.getItem('anilux_refresh_token_v1') !== refreshToken) throw new CanceledError('Login session changed');
      const { access, refresh } = response.data;
      localStorage.setItem("anilux_access_token_v1", access);
      if (refresh) {
        localStorage.setItem("anilux_refresh_token_v1", refresh);
      }
      return access;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

apiClient.interceptors.request.use((config) => {
  if (config._accountId !== undefined) {
    let owner: unknown;
    try { owner = JSON.parse(localStorage.getItem('anilux_user_v1') || 'null')?.id; } catch { /* invalid session */ }
    if (String(owner) !== config._accountId) throw new CanceledError('Login session changed');
  }
  config._sessionRefresh = localStorage.getItem("anilux_refresh_token_v1");
  const token = localStorage.getItem("anilux_access_token_v1");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const status = error.response?.status;
    if (status && status >= 500) {
      console.error(`API ${status}:`, originalRequest?.url);
    } else if (status && status >= 400 && originalRequest?.method !== "get") {
      console.error(
        `API ${status}:`,
        originalRequest?.url,
        error.response?.data,
      );
    }

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !originalRequest.url?.includes("/token/refresh/")) {
      if (originalRequest._sessionRefresh !== localStorage.getItem('anilux_refresh_token_v1')) return Promise.reject(new CanceledError('Login session changed'));
      if (!originalRequest._sessionRefresh) return Promise.reject(error);
      originalRequest._retry = true;

      const originalRefresh = localStorage.getItem('anilux_refresh_token_v1');
      try {
        const access = await getRefreshedAccessToken();
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        if (axios.isCancel(refreshError) || localStorage.getItem('anilux_refresh_token_v1') !== originalRefresh) return Promise.reject(refreshError);
        const refreshStatus = axios.isAxiosError(refreshError) ? refreshError.response?.status : undefined;
        if (localStorage.getItem("anilux_refresh_token_v1") && ![400, 401, 403].includes(refreshStatus ?? 0)) {
          return Promise.reject(refreshError);
        }
        const [outbox, globalSocket, privateChats, groupChats, extras, folders] = await Promise.all([
          import('@/lib/chatOutbox'),
          import('@/composables/useGlobalWebSocket'),
          import('@/stores/privateChat'),
          import('@/stores/groupChat'),
          import('@/stores/chatExtras'),
          import('@/stores/chatFolders'),
        ]);
        outbox.clearChatOutbox();
        localStorage.removeItem("anilux_access_token_v1");
        localStorage.removeItem("anilux_refresh_token_v1");
        localStorage.removeItem("anilux_user_v1");
        window.dispatchEvent(new Event("anilux-auth-session-invalidated"));
        globalSocket.disconnectGlobalWebSocket();
        privateChats.usePrivateChatStore().clearChats();
        groupChats.useGroupChatStore().clearGroupChats();
        extras.useChatExtrasStore().clearAllData();
        folders.useChatFoldersStore().clearFolders();
        const publicPaths = ["/anime", "/anime/", "/"];
        const isPublicPage = publicPaths.some((p) =>
          p === "/" ? window.location.pathname === p : window.location.pathname.startsWith(p),
        );
        if (!isPublicPage) {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export const get = <T>(url: string, config?: AxiosRequestConfig) =>
  apiClient.get<T>(url, config);

export const post = <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
) => apiClient.post<T>(url, data, config);

export const put = <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
) => apiClient.put<T>(url, data, config);

export const patch = <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
) => apiClient.patch<T>(url, data, config);

export const remove = (url: string, config?: AxiosRequestConfig) =>
  apiClient.delete(url, config);

export { apiClient };
export default apiClient;

export const getWebSocketUrl = (path: string): string => {
  const base = baseURL.replace(/\/api$/, "");

  const protocol =
    window.location.protocol === "https:" ? "wss:" : "ws:";

  const host = base.replace(/^https?:\/\//, "").replace(/\/$/, "");

  return `${protocol}//${host}${path.startsWith("/") ? "" : "/"}${path}`;
};
