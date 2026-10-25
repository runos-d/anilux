from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from rest_framework.routers import DefaultRouter
from django.conf import settings
from config.disabled_features import disabled_feature

from . import views
from . import views_library
from . import views_subscription
from .views.auth_views import SafeTokenRefreshView
from apps.social.presentation.views.views_support import SupportTicketViewSet

try:
    from config import views_admin
except ImportError:
    views_admin = None

router = DefaultRouter()
router.register(
    r"profile-settings", views.UserProfileSettingsViewSet, basename="profile-settings"
)
router.register(
    r"notification-settings",
    views.NotificationSettingsViewSet,
    basename="notification-settings",
)
router.register(
    r"privacy-settings", views.PrivacySettingsViewSet, basename="privacy-settings"
)
router.register(r"themes", views.UserThemeViewSet, basename="themes")
router.register(
    r"chat-backgrounds", views.ChatBackgroundViewSet, basename="chat-backgrounds"
)
router.register(r"analytics", views.UserAnalyticsViewSet, basename="analytics")
router.register(r"library", views.UserLibraryViewSet, basename="library")
router.register(r"favorites", views_library.UserFavoritesViewSet, basename="favorites")
router.register(
    r"favorite_themes", views_library.FavoriteThemesViewSet, basename="favorite-themes"
)
router.register(
    r"favorite_episodes",
    views_library.FavoriteEpisodesViewSet,
    basename="favorite-episodes",
)

urlpatterns = [
    path("library/wrapped/", views.UserWrappedView.as_view(), name="library_wrapped"),
    path("", include(router.urls)),
    path("me/", views.CurrentUserView.as_view(), name="current_user"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", SafeTokenRefreshView.as_view(), name="token_refresh"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("google/", views.GoogleAuthView.as_view(), name="google_auth"),
    path(
        "google/callback/",
        views.GoogleAuthCallbackView.as_view(),
        name="google_auth_callback",
    ),
    path("google/exchange/", views.GoogleAuthExchangeView.as_view(), name="google_auth_exchange"),
    path(
        "verify/email/",
        views.EmailVerificationView.as_view(),
        name="email_verification",
    ),
    path("confirm-email/", views.EmailConfirmView.as_view(), name="email_confirm"),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    path(
        "profile/<int:pk>/",
        views.UserPublicProfileView.as_view(),
        name="user_public_profile",
    ),
    path(
        "by-nickname/<str:nickname>/",
        views.UserProfileByNicknameView.as_view(),
        name="user_by_nickname",
    ),
    path(
        "admin/dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"
    ),
    path(
        "admin/complaints/",
        views.AdminComplaintsView.as_view(),
        name="admin_complaints",
    ),
    path(
        "admin/complaints/<int:complaint_id>/",
        views.AdminComplaintsView.as_view(),
        name="admin_complaint_detail",
    ),
    path(
        "admin/posts/<int:post_id>/",
        views.AdminDeletePostView.as_view(),
        name="admin_delete_post",
    ),
    path("password-reset/", views.password_reset, name="password_reset"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("profile/update/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path("settings/", views.UserSettingsView.as_view(), name="user_settings"),
    path("avatar/", views.AvatarUploadView.as_view(), name="avatar_upload"),
    path(
        "avatar/from-screenshot/",
        views.AvatarFromScreenshotView.as_view(),
        name="avatar_from_screenshot",
    ),
    path(
        "cover/from-screenshot/",
        views.CoverFromScreenshotView.as_view(),
        name="cover_from_screenshot",
    ),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),
    path("sessions/", views.UserSessionsView.as_view(), name="user_sessions"),
    path(
        "sessions/<int:pk>/",
        views.UserSessionDetailView.as_view(),
        name="user_session_detail",
    ),
    path("nickname/check/", views.NicknameCheckView.as_view(), name="nickname_check"),
    path(
        "sessions/active/",
        views.SessionViewSet.as_view({"get": "list"}),
        name="active_sessions",
    ),
    path(
        "sessions/terminate/",
        views.SessionViewSet.as_view({"post": "terminate"}),
        name="terminate_session",
    ),
    path(
        "sessions/terminate-all/",
        views.SessionViewSet.as_view({"post": "terminate_all_others"}),
        name="terminate_all_sessions",
    ),
    path(
        "account-deletion/",
        views.AccountDeletionView.as_view(),
        name="account_deletion",
    ),
    path("theme-settings/", views.ThemeSettingsView.as_view(), name="theme_settings"),
    path(
        "chat-background-settings/",
        views.ChatBackgroundSettingsView.as_view(),
        name="chat_background_settings",
    ),
    path("font-settings/", views.FontSettingsView.as_view(), name="font_settings"),
    path("storage-usage/", views.StorageUsageView.as_view(), name="storage_usage"),
    path("sync-settings/", views.SyncSettingsView.as_view(), name="sync_settings"),
    path("export-data/", views.ExportDataView.as_view(), name="export_data"),
    path("clear-cache/", views.ClearCacheView.as_view(), name="clear_cache"),
    path("online/", views.OnlineUsersView.as_view(), name="online_users"),
    path("realtime/", views.RealtimeUpdatesView.as_view(), name="realtime_updates"),
    path("search/", views.UserSearchView.as_view(), name="user_search"),
    path("<int:user_id>/feed/", views.UserFeedView.as_view(), name="user_feed"),
    path("<int:pk>/stats/", views.UserStatsView.as_view(), name="user_stats"),
    path(
        "<str:pk>/stats/", views.UserStatsView.as_view(), name="user_stats_by_username"
    ),
    path("settings/all/", views.AllSettingsView.as_view(), name="all_settings"),
    path("users/", views.UsersListView.as_view(), name="users_list"),
    path("online-status/", views.OnlineStatusView.as_view(), name="online_status"),
    path("heartbeat/", views.HeartbeatView.as_view(), name="heartbeat"),
    path(
        "support/tickets/",
        SupportTicketViewSet.as_view({"get": "list", "post": "create"}),
        name="support_tickets",
    ),
    path(
        "support/tickets/<int:pk>/",
        SupportTicketViewSet.as_view({"get": "retrieve"}),
        name="support_ticket_detail",
    ),
    path(
        "support/tickets/<int:pk>/reply/",
        SupportTicketViewSet.as_view({"post": "reply"}),
        name="support_ticket_reply",
    ),
    path(
        "support/tickets/<int:pk>/close/",
        SupportTicketViewSet.as_view({"post": "close"}),
        name="support_ticket_close",
    ),
    path(
        "support/tickets/<int:pk>/reopen/",
        SupportTicketViewSet.as_view({"post": "reopen"}),
        name="support_ticket_reopen",
    ),
    path(
        "support/tickets/<int:pk>/mark-read/",
        SupportTicketViewSet.as_view({"post": "mark_read"}),
        name="support_ticket_mark_read",
    ),
    path(
        "support/unread-count/",
        SupportTicketViewSet.as_view({"get": "unread_count"}),
        name="support_unread_count",
    ),
    path(
        "subscription/",
        views_subscription.SubscriptionView.as_view(),
        name="subscription",
    ),
    path(
        "subscription/activate/",
        views_subscription.SubscriptionActivateView.as_view(),
        name="subscription_activate",
    ),
    path(
        "promo_validate/",
        views_subscription.PromoCodeValidateView.as_view(),
        name="promo_validate",
    ),
]

urlpatterns.append(re_path(r"^2fa(?:/.*)?$", disabled_feature))

urlpatterns.append(re_path(r"^verify/phone(?:/.*)?$", disabled_feature))

if settings.DEBUG:
    urlpatterns.extend([
        path("headers-debug/", views.HeadersDebugView.as_view(), name="headers_debug"),
        path("auth-debug/", views.AuthDebugView.as_view(), name="auth_debug"),
    ])
else:
    urlpatterns.extend([
        path("headers-debug/", disabled_feature, name="headers_debug_disabled"),
        path("auth-debug/", disabled_feature, name="auth_debug_disabled"),
    ])
