<template>
  <aside
    class="sidebar"
    :class="{ collapsed: isCollapsed }"
  >
    <div class="sakura-decor">
      <span class="petal petal-1"><SakuraIcon name="flower" /></span>
      <span class="petal petal-2"><SakuraIcon name="flower" /></span>
    </div>

    <div class="sidebar-header">
      <router-link to="/" class="sidebar-logo">
        <span class="logo-icon" v-html="logoSvg"></span>
        <span class="logo-text">AniLux</span>
      </router-link>
      <button
        @click="toggleSidebar"
        class="collapse-btn"
        type="button"
        :aria-expanded="!isCollapsed"
        :aria-label="isCollapsed ? 'Развернуть меню' : 'Свернуть меню'"
        :title="isCollapsed ? 'Развернуть' : 'Свернуть'"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          :class="{ rotated: isCollapsed }"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: isActiveRoute('/') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
        </span>
        <span class="nav-label">Главная</span>
      </router-link>

      <router-link to="/feed" class="nav-item" :class="{ active: isActiveRoute('/feed') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
        </span>
        <span class="nav-label">Лента</span>
      </router-link>

      <router-link to="/anime" class="nav-item" :class="{ active: isActiveRoute('/anime') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
            <line x1="7" y1="2" x2="7" y2="22" />
            <line x1="17" y1="2" x2="17" y2="22" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <line x1="2" y1="7" x2="7" y2="7" />
            <line x1="2" y1="17" x2="7" y2="17" />
            <line x1="17" y1="7" x2="22" y2="7" />
            <line x1="17" y1="17" x2="22" y2="17" />
          </svg>
        </span>
        <span class="nav-label">Аниме</span>
      </router-link>

      <router-link to="/playlists" class="nav-item" :class="{ active: isActiveRoute('/playlists') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </span>
        <span class="nav-label">Плейлисты</span>
      </router-link>

      <router-link to="/roulette" class="nav-item" :class="{ active: isActiveRoute('/roulette') }">
        <span class="nav-icon"><SakuraIcon name="wheel" /></span>
        <span class="nav-label">Рулетка</span>
      </router-link>

      <router-link to="/library" class="nav-item" :class="{ active: isActiveRoute('/library') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
        </span>
        <span class="nav-label">Моя коллекция</span>
      </router-link>

      <router-link to="/chats" class="nav-item" :class="{ active: isActiveRoute('/chats') }">
        <span class="nav-icon">
          <span class="chat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
            </svg>
            <span v-if="unreadCount > 0" class="unread-badge">
              {{ unreadCount > 99 ? "99+" : unreadCount }}
            </span>
          </span>
        </span>
        <span class="nav-label">Чаты</span>
      </router-link>

      <router-link to="/people" class="nav-item" :class="{ active: isActiveRoute('/people') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        </span>
        <span class="nav-label">Люди</span>
      </router-link>

      <router-link to="/ideas" class="nav-item" :class="{ active: isActiveRoute('/ideas') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18h6" />
            <path d="M10 22h4" />
            <path d="M8.4 14.5A7 7 0 1 1 15.6 14.5c-.7.5-1.1 1.3-1.1 2.1h-5c0-.8-.4-1.6-1.1-2.1Z" />
          </svg>
        </span>
        <span class="nav-label">Идеи</span>
      </router-link>

      <router-link to="/history" class="nav-item" :class="{ active: isActiveRoute('/history') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
            <path d="M3 3v5h5M12 7v5l3 2" />
          </svg>
        </span>
        <span class="nav-label">История</span>
      </router-link>
      
      <router-link :to="profileLink" class="nav-item" :class="{ active: isProfileActive }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </span>
        <span class="nav-label">Профиль</span>
      </router-link>
    </nav>

    <div class="sidebar-divider"></div>

    <nav class="sidebar-nav-secondary">
      <router-link to="/achievements" class="nav-item-secondary" :class="{ active: isActiveRoute('/achievements') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
            <path d="M4 22h16" />
            <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
            <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
            <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
          </svg>
        </span>
        <span class="nav-label">Достижения</span>
      </router-link>

      <router-link to="/settings" class="nav-item-secondary" :class="{ active: isActiveRoute('/settings') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </span>
        <span class="nav-label">Настройки</span>
      </router-link>

      <router-link to="/app" class="nav-item-secondary" :class="{ active: isActiveRoute('/app') }">
        <span class="nav-icon"><SakuraIcon name="download" /></span>
        <span class="nav-label">Приложение</span>
      </router-link>

      <router-link v-if="isAdmin" to="/admin" class="nav-item-secondary nav-item-admin" :class="{ active: isActiveRoute('/admin') }">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </span>
        <span class="nav-label">Админ</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from "vue";
import { afterInitialContent } from "@/lib/initialContent";
import { useRoute } from "vue-router";
import { useSidebar } from "@/composables/useSidebar";
import { useAuthStore } from "@/stores/auth";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { logoSvg } from "@/assets/logoSvg";
import SakuraIcon from "../icons/SakuraIcon.vue";

const route = useRoute();
const { isCollapsed, toggleSidebar } = useSidebar();
const authStore = useAuthStore();
const chatExtrasStore = useChatExtrasStore();

const isAdmin = computed(() => {
  const u = authStore.user;
  if (!u) return false;
  return u.is_admin || u.is_staff;
});

const isActiveRoute = (path: string) => {
  if (path === "/") return route.path === "/";
  return route.path === path || route.path.startsWith(path + "/");
};

const profileLink = computed(() => {
  const userId = authStore.user?.id;
  return userId ? `/profile/${userId}` : "/profile";
});

const isProfileActive = computed(
  () => route.path.startsWith("/profile/") || route.path === "/profile",
);

const unreadCount = computed(() => chatExtrasStore.totalUnreadCount || 0);

let unreadInterval: number | null = null;
const refreshUnreadOnForeground = () => {
  if (document.visibilityState === "visible" && authStore.isAuthenticated)
    void chatExtrasStore.loadUnreadChats();
};

onMounted(() => {
  afterInitialContent(() => {
    if (authStore.isAuthenticated) void chatExtrasStore.loadUnreadChats();
  });
  unreadInterval = window.setInterval(refreshUnreadOnForeground, 5 * 60 * 1000);
  document.addEventListener("visibilitychange", refreshUnreadOnForeground);
});

onBeforeUnmount(() => {
  if (unreadInterval) {
    clearInterval(unreadInterval);
    unreadInterval = null;
  }
  document.removeEventListener("visibilitychange", refreshUnreadOnForeground);
});
</script>

<style scoped>
.sidebar {
  --sb-collapsed-w: var(--sidebar-width-collapsed, 64px);
  --sb-icon-col: 64px;
  --sb-dur: var(--sb-transition-duration, 280ms);
  --sb-ease: var(--sb-transition-ease, ease-out);

  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width, 280px);
  height: 100vh;
  background: linear-gradient(
    180deg,
    var(--panel-sidebar) 0%,
    color-mix(in srgb, var(--panel-sidebar) 85%, var(--surface-0)) 100%
  );
  border-right: 1px solid var(--border-subtle);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  /* Изолируем layout/style/paint — перерисовка сайдбара не задевает остальную страницу */
  contain: layout style paint;

  transition: width var(--sb-dur) var(--sb-ease);
}

.sidebar.collapsed {
  width: var(--sb-collapsed-w);
}

/* ── Декорация ── */
.sakura-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  opacity: 0.15;
  transition: opacity var(--sb-dur) var(--sb-ease);
}
.petal {
  position: absolute;
  font-size: 12px;
  animation: floatPetal 8s ease-in-out infinite;
  /* filter: blur(0.5px) убран — дорогой эффект при непрерывной анимации,
     визуально на 12px практически не заметен */
  backface-visibility: hidden;
}
.petal-1 { top: 20%; right: 10%; animation-delay: -2s; }
.petal-2 { top: 60%; right: 5%; animation-delay: -4s; font-size: 10px; }

/* GPU-подсказка только пока лепестки реально анимируются */
.sidebar:not(.collapsed) .petal {
  will-change: transform, opacity;
}

/* В свёрнутом состоянии — пауза, чтобы не жечь CPU/GPU */
.sidebar.collapsed .petal {
  animation-play-state: paused;
}

@keyframes floatPetal {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.1; }
  25% { transform: translateY(-8px) rotate(5deg); opacity: 0.2; }
  50% { transform: translateY(-4px) rotate(-3deg); opacity: 0.15; }
  75% { transform: translateY(-10px) rotate(2deg); opacity: 0.1; }
}

.sidebar.collapsed .sakura-decor { opacity: 0.05; }

/* ── Header ── */
.sidebar-header {
  height: var(--navbar-height);
  display: flex;
  align-items: center;
  padding: 0;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.sidebar-logo {
  text-decoration: none;
  display: flex;
  align-items: center;
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
}

.logo-icon {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: var(--sb-icon-col);
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 120ms ease;
}

.logo-icon :deep(svg) {
  transform-origin: center;
  transition: transform 260ms var(--sb-ease);
}
.sidebar-logo:hover .logo-icon :deep(svg) {
  transform: rotate(22deg) scale(1.04);
}

.logo-text {
  position: absolute;
  left: calc(var(--sb-icon-col) - 8px);
  top: 50%;
  transform: translateY(-50%) translateX(0);
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.025em;
  white-space: nowrap;
  color: var(--text-primary);
  opacity: 1;
  transition:
    opacity 220ms var(--sb-ease),
    transform 220ms var(--sb-ease);
  transition-delay: 40ms;
}

.sidebar.collapsed .logo-text {
  opacity: 0;
  transform: translateY(-50%) translateX(-6px);
  transition-delay: 0ms;
}

.sidebar.collapsed .logo-icon {
  opacity: 0;
}

.collapse-btn {
  position: absolute;
  top: 50%;
  right: calc((var(--sb-collapsed-w) - 28px) / 2);
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-height: 28px;
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition:
    color 150ms ease,
    background-color 150ms ease,
    border-color 150ms ease,
    box-shadow 150ms ease;
  flex-shrink: 0;
  z-index: 2;
}

.collapse-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
  border-color: var(--accent);
  box-shadow: var(--shadow-sm-glow-sm);
}

.collapse-btn svg {
  transition: transform 200ms var(--sb-ease);
}
.collapse-btn svg.rotated {
  transform: rotate(180deg);
}

/* ── Навигация ── */
.sidebar-nav,
.sidebar-nav-secondary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 0;
  position: relative;
  z-index: 1;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain; /* не скроллим страницу за сайдбаром */
}

.sidebar-nav-secondary {
  flex-shrink: 0;
  padding-bottom: 12px;
}

.nav-item,
.nav-item-secondary {
  position: relative;
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  /* убран лишний background-color transition (фон живёт на ::after) */
  transition: color 150ms ease;
}

.nav-item-secondary {
  height: 38px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  border-radius: var(--radius-md);
}

/* Иконка — абсолютная, никогда не двигается */
.nav-icon {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: var(--sb-icon-col);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}

.nav-icon svg {
  opacity: 0.7;
  transition: opacity 150ms ease, color 150ms ease;
  flex-shrink: 0;
}

.nav-item:hover .nav-icon svg,
.nav-item.active .nav-icon svg,
.nav-item-secondary:hover .nav-icon svg,
.nav-item-secondary.active .nav-icon svg {
  opacity: 1;
  color: var(--accent);
}

/* Лейбл — абсолютный, скрывается через opacity+transform */
.nav-label {
  position: absolute;
  left: 55px;
  top: 50%;
  transform: translateY(-50%) translateX(0);
  opacity: 1;
  z-index: 1; 
  transition:
    opacity 200ms var(--sb-ease),
    transform 200ms var(--sb-ease);
  transition-delay: 40ms;
  pointer-events: none;
}

.sidebar.collapsed .nav-label {
  opacity: 0;
  transform: translateY(-50%) translateX(-6px);
  transition-delay: 0ms;
}

.nav-item::after,
.nav-item-secondary::after {
  content: "";
  position: absolute;
  inset: 0 8px;
  border-radius: inherit;
  background: transparent;
  transition: background-color 150ms ease;
  pointer-events: none;
  z-index: 0;
}

.nav-item:hover::after,
.nav-item-secondary:hover::after {
  background-color: var(--surface-4);
}

.nav-item:hover,
.nav-item-secondary:hover {
  color: var(--text-primary);
}

.nav-item.active::after {
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.nav-item.active { color: var(--accent); }
.nav-item-secondary.active { color: var(--accent); }
.nav-item-secondary.active::after { background: var(--accent-subtle); }

.nav-item.active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  z-index: 2;
}

.chat-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.unread-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  font-size: 10px;
  font-weight: 700;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--surface-2);
  white-space: nowrap;
  z-index: 1;
  box-shadow: var(--shadow-sm-petal-sm);
}

.sidebar-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--border-subtle) 50%,
    transparent 100%
  );
  margin: 8px 12px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.nav-item-admin { color: var(--danger) !important; }
.nav-item-admin:hover::after { background: var(--danger-subtle) !important; }
.nav-item-admin.active::after { background: var(--danger-subtle) !important; }

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .logo-icon :deep(svg),
  .logo-text,
  .nav-label,
  .collapse-btn,
  .collapse-btn svg,
  .sakura-decor,
  .petal {
    transition-duration: 0.01ms !important;
    animation: none !important;
  }
}

@media (max-width: 1023px) {
  .sidebar { overflow-y: auto; }
}
@media (max-width: 767px) {
  .sidebar { display: none; }
}
</style>
