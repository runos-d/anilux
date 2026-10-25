import { refreshSeo } from "@/composables/useSeo";
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { cancelAllRequests } from "@/api/client";
import { queryClient } from '@/lib/queryClient';
import { cancelInitialReads } from '@/lib/initialRead';
import { features } from '@/config/features';
const HomeView = () => import("@/components/page/other/HomeView.vue")
const LoginView = () => import("@/components/page/auth/LoginView.vue")
const RegisterView = () => import("@/components/page/auth/RegisterView.vue")
const AnimeView = () => import("@/components/page/anime/AnimeView.vue")
const AnimeDetailView = () => import("@/components/page/anime/AnimeDetailView.vue")
const FranchiseView = () => import("@/components/page/anime/FranchiseView.vue")
const AnimeWatchView = () => import("@/components/page/anime/AnimeWatchView.vue")
const OwnProfileView = () => import("@/components/page/profile/OwnProfileView.vue")
const UserProfileView = () => import("@/components/page/profile/UserProfileView.vue")
const FeedView = () => import("@/components/page/feed/FeedView.vue")
const PostDetailView = () => import("@/components/page/feed/PostDetailView.vue")
const ChatsView = () => import("@/components/page/chats/ChatsView.vue")
const PlaylistsView = () => import("@/components/page/playlists/PlaylistsView.vue")
const PlaylistDetailView = () => import("@/components/page/playlists/PlaylistDetailView.vue")
const MyPlaylistsView = () => import("@/components/page/playlists/MyPlaylistsView.vue")
const CreatePlaylistView = () => import("@/components/page/playlists/CreatePlaylistView.vue")
const PublicPlaylistsView = () => import("@/components/page/playlists/PublicPlaylistsView.vue")
const NotificationsView = () => import("@/components/page/notifications/NotificationsView.vue")
const NotificationSettingsView = () => import("@/components/page/notifications/NotificationSettingsView.vue")
const SettingsView = () => import("@/components/page/settings/SettingsView.vue")
const KodikImport = () => import("@/components/page/admin/KodikImport.vue")
const AddAnimeView = () => import("@/components/page/other/AddAnimeView.vue")
const UserLibraryView = () => import("@/components/page/profile/UserLibraryView.vue")
const UserStatsView = () => import("@/components/page/profile/UserStatsView.vue")
const WatchHistoryView = () => import("@/components/page/profile/WatchHistoryView.vue")
const AchievementsView = () => import("@/components/page/other/AchievementsView.vue")
const PeopleView = () => import("@/components/page/people/PeopleView.vue")
const PeopleDetailView = () => import("@/components/page/people/PeopleDetailView.vue")
const SharedPlaylistView = () => import("@/components/page/playlists/SharedPlaylistView.vue")
const DonateView = () => import("@/components/page/other/DonateView.vue")
const CreateGroupView = () => import("@/components/page/chats/CreateGroupView.vue")
const GroupsView = () => import("@/components/page/chats/GroupsView.vue")
const AnnouncementDetailView = () => import("@/components/page/other/AnnouncementDetailView.vue")
const ModerationView = () => import("@/components/page/admin/ModerationView.vue")
const NewsView = () => import("@/components/page/other/NewsView.vue")
const ChatInviteView = () => import("@/components/page/chats/ChatInviteView.vue")
const IdeasView = () => import("@/components/page/ideas/IdeasView.vue")
const RouletteView = () => import("@/components/page/anime/RouletteView.vue")

const visualTestRoutes = import.meta.env.DEV || import.meta.env.MODE === 'visual' ? [
  {
    path: '/__visual__/modals',
    name: 'visual-modal-gallery',
    component: () => import('@/dev/VisualModalGallery.vue'),
    meta: { hideAppNav: true },
  },
] : []

const optionalFeatureRoutes = [
  ...(features.dubs ? [
    { path: '/people/:id', name: 'people-detail', component: PeopleDetailView, props: true },
  ] : []),
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, behavior: 'smooth' };
    return { top: 0, left: 0 };
  },
  routes: [
    { path: '/contacts', name: 'contacts', component: () => import('@/components/page/other/ContactsPage.vue') },
    { path: '/terms', name: 'terms', component: () => import('@/components/page/other/TermsPage.vue') },
    { path: '/privacy', name: 'privacy', component: () => import('@/components/page/other/PrivacyPage.vue') },
    { path: '/license', name: 'license', component: () => import('@/components/page/other/LicensePage.vue') },
    { path: '/app', name: 'application', component: () => import('@/components/page/other/ApplicationView.vue') },
    { path: '/excerpts', name: 'excerpts', component: () => import('@/components/page/excerpts/ExcerptsView.vue'), meta: { requiresAuth: true } },
    { path: '/excerpts/s/:token', name: 'excerpt-shared', component: () => import('@/components/page/excerpts/ExcerptView.vue') },
    { path: '/excerpts/:id', name: 'excerpt', component: () => import('@/components/page/excerpts/ExcerptView.vue'), meta: { requiresAuth: true } },
    {
      path: "",
      name: "home",
      component: HomeView,
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { requiresGuest: true },
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: { requiresGuest: true },
    },
    { path: '/confirm-email', name: 'confirm-email', component: () => import('@/components/page/auth/ConfirmEmailView.vue'), meta: { requiresGuest: true } },
    { path: '/reset-password', name: 'reset-password', component: () => import('@/components/page/auth/ResetPasswordView.vue'), meta: { requiresGuest: true } },
    { path: '/oauth/callback', name: 'oauth-callback', component: () => import('@/components/page/auth/OAuthCallbackView.vue'), meta: { requiresGuest: true } },
    {
      path: "/anime",
      name: "anime-catalog",
      component: AnimeView,
    },
    {
      path: "/roulette",
      name: "roulette",
      component: RouletteView,
    },
    {
      path: "/anime/ongoings",
      name: "anime-ongoings",
      redirect: () => ({ path: "/anime", query: { section: "ongoings" } }),
    },
    {
      path: "/anime/announcements",
      name: "anime-announcements",
      redirect: () => ({ path: "/anime", query: { section: "announcements" } }),
    },
    {
      path: "/anime/calendar",
      name: "anime-calendar-preset",
      redirect: () => ({ path: "/anime", query: { section: "calendar" } }),
    },
    {
      path: "/anime/watching",
      name: "anime-watching-preset",
      redirect: () => ({ path: "/anime", query: { section: "currently_watching" } }),
    },
    {
      path: "/anime/year/:year",
      name: "anime-year",
      component: () => import('@/components/page/anime/SeoCollectionView.vue'),
      props: (route) => ({ presetYear: Number(route.params.year) }),
    },
    {
      path: "/anime/genre/:genre",
      name: "anime-genre",
      component: () => import('@/components/page/anime/SeoCollectionView.vue'),
      props: (route) => ({ presetGenre: route.params.genre }),
    },
    {
      path: "/anime/type/:kind",
      name: "anime-type",
      component: () => import('@/components/page/anime/SeoCollectionView.vue'),
      props: (route) => ({ presetKind: route.params.kind }),
    },
    {
      path: "/anime/status/:status",
      name: "anime-status",
      component: () => import('@/components/page/anime/SeoCollectionView.vue'),
      props: (route) => ({ presetStatus: route.params.status }),
    },
    {
      path: "/anime/franchise/:slug",
      name: "anime-franchise",
      component: FranchiseView,
      props: (route) => ({ presetSlug: route.params.slug }),
    },
    {
      path: "/anime/season/:year/:season",
      name: "anime-season",
      component: () => import('@/components/page/anime/SeoCollectionView.vue'),
      props: (route) => ({ presetYear: Number(route.params.year), presetSeason: route.params.season }),
    },
    { path: '/anime/browse', component: () => import('@/components/page/anime/SeoCollectionView.vue') },
    { path: '/anime/collection/:slug', component: () => import('@/components/page/anime/SeoCollectionView.vue') },
    { path: '/anime/:slug([0-9]+)-:label', name: 'anime-canonical', component: AnimeDetailView,
      props: route => ({ slug: route.params.slug }) },
    {
      path: "/anime/:slug",
      name: "anime-detail",
      component: AnimeDetailView,
      props: (route) => ({ slug: route.params.slug }),
    },
    {
      path: "/franchise/:slug",
      name: "franchise-detail",
      component: FranchiseView,
      props: (route) => ({ slug: route.params.slug }),
    },
    {
      path: "/anime/:slug/watch",
      name: "anime-watch",
      component: AnimeWatchView,
      props: (route) => ({ slug: route.params.slug }),
    },
    {
      path: "/profile",
      name: "profile",
      component: OwnProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: "/profile/@:nickname",
      name: "user-profile-by-nickname",
      component: UserProfileView,
      props: (route) => ({ nickname: route.params.nickname }),
    },
    {
      path: "/profile/:id",
      name: "user-profile",
      component: UserProfileView,
      props: true,
    },
    {
      path: "/people",
      name: "people",
      component: PeopleView,
    },
    {
      path: "/@:nickname",
      name: "user-short-nickname",
      component: UserProfileView,
      props: (route) => ({ nickname: route.params.nickname }),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("@/components/page/admin/AdminDashboard.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/admin/complaints",
      name: "admin-complaints",
      component: () => import("@/components/page/admin/AdminDashboard.vue"),
      props: { tab: "complaints" },
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/admin/franchises",
      name: "admin-franchises",
      component: () => import("@/components/page/admin/AdminDashboard.vue"),
      props: { tab: "franchises" },
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/achievements",
      name: "achievements",
      component: AchievementsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/feed",
      name: "feed",
      component: FeedView,
      meta: { requiresAuth: true },
    },
    {
      path: "/news",
      name: "news",
      component: NewsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/ideas",
      name: "ideas",
      component: IdeasView,
    },
    {
      path: "/post/:id",
      name: "post-detail",
      component: PostDetailView,
      props: true,
    },
    {
      path: "/chats",
      name: "chats",
      component: ChatsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/groups",
      name: "chats-groups",
      component: GroupsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/create-group",
      name: "chats-create-group",
      component: CreateGroupView,
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/:code([0-9]{8})",
      name: "chat-by-code",
      component: ChatsView,
      props: (route) => ({ slug: String(route.params.code) }),
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/:id([0-9a-fA-F-]{36})/topic/:slug",
      name: "chat-topic",
      component: ChatsView,
      props: (route) => ({ slug: String(route.params.id), topicSlug: route.params.slug }),
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/:id([0-9]+)/topic/:slug",
      name: "chat-topic-int",
      component: ChatsView,
      props: (route) => ({ slug: String(route.params.id), topicSlug: route.params.slug }),
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/:id([0-9a-fA-F-]{36})",
      name: "chat-by-id",
      component: ChatsView,
      props: (route) => ({ slug: route.params.id }),
      meta: { requiresAuth: true },
    },
    {
      path: "/chats/:slug?",
      name: "chats-detail",
      component: ChatsView,
      props: (route) => ({ slug: route.params.slug || null }),
      meta: { requiresAuth: true },
    },
    {
      path: "/playlists",
      name: "playlists",
      component: PlaylistsView,
    },
    {
      path: "/playlists/create",
      name: "create-playlist",
      component: CreatePlaylistView,
      meta: { requiresAuth: true },
    },
    {
      path: "/playlists/:id/edit",
      name: "edit-playlist",
      component: CreatePlaylistView,
      meta: { requiresAuth: true },
      props: true,
    },
    {
      path: "/my-playlists",
      name: "my-playlists",
      component: MyPlaylistsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/public-playlists",
      name: "public-playlists",
      component: PublicPlaylistsView,
    },
    {
      path: "/add-anime",
      name: "add-anime",
      component: AddAnimeView,
    },
    {
      path: "/library",
      name: "library",
      component: UserLibraryView,
      meta: { requiresAuth: true },
    },
    {
      path: "/stats",
      name: "stats",
      component: UserStatsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/history",
      name: "watch-history",
      component: WatchHistoryView,
      meta: { requiresAuth: true },
    },
    {
      path: "/playlist/:id",
      name: "playlist-detail",
      component: PlaylistDetailView,
      props: true,
    },
    {
      path: "/playlist/shared/:token",
      name: "playlist-shared",
      component: SharedPlaylistView,
      props: true,
    },
    {
      path: "/notifications",
      name: "notifications",
      component: NotificationsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/notifications/settings",
      name: "notification-settings",
      component: NotificationSettingsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/settings",
      name: "settings",
      component: SettingsView,
      meta: { requiresAuth: true },
    },
    {
      path: "/admin/kodik-import",
      name: "kodik-import",
      component: KodikImport,
      meta: { requiresAuth: true },
    },
    ...optionalFeatureRoutes,
    {
      path: "/announcements/:slug",
      name: "announcement-detail",
      component: AnnouncementDetailView,
      props: (route) => ({ slug: route.params.slug }),
    },
    {
      path: "/donate",
      name: "donate",
      component: DonateView,
    },
    {
      path: "/subscription",
      name: "subscription",
      redirect: "/donate",
    },
    {
      path: "/moderation",
      name: "moderation",
      component: ModerationView,
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/chats/invite/:token([a-zA-Z0-9_-]{10,})",
      alias: "/:token([a-zA-Z0-9_-]{10,})",
      name: "chat-invite",
      component: ChatInviteView,
      props: (route) => ({ token: route.params.token }),
    },
    ...visualTestRoutes,
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/components/page/other/NotFoundView.vue') },
  ],
});

router.afterEach((to) => { void refreshSeo(to.fullPath); });

router.beforeEach(async (to, from, next) => {
  if (to.path !== from.path) {
    cancelAllRequests();
    cancelInitialReads();
    void queryClient.cancelQueries();
  }
  const authStore = useAuthStore();

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      try {
        await authStore.checkAuth();
        if (!authStore.isAuthenticated) {
          next("/login");
          return;
        }
      } catch {
        next("/login");
        return;
      }
    }
  }

  if (to.matched.some((record) => record.meta.requiresGuest)) {
    if (authStore.isAuthenticated && !authStore.isLocalDevelopment()) {
      next("/anime");
      return;
    }
  }

  if (to.matched.some((record) => record.meta.requiresAdmin)) {
    const u = authStore.user;
    const isAdmin =
      u && (u.is_admin || u.is_staff);
    if (!isAdmin) {
      next("/");
      return;
    }
  }

  next();
});

export default router;
