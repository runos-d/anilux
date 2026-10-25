from .views.group_settings import group_settings
from .views.chat_media import chat_media
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.social.application._discussion_views_patch import get_anime_discussion_group
from apps.social.presentation.views.views_feed import FeedViewSet

from apps.social.presentation.views.social_views import (
    CommentListCreateView,
    CommentDetailView,
    GroupViewSet,
    PostCommentViewSet,
    PostViewSet,
    CombinedChatsView,
    GroupChatViewSet,
    ChatRoleViewSet,
    PrivateChatViewSet,
    get_chat_detail,
    FollowViewSet,
    get_post_likers,
    get_unread_count,
    get_unread_chats,
    mark_chat_read,
    MessageListCreateView,
    MessageDetailView,
    edit_message,
    delete_message,
    mark_message_read,
    toggle_comment_like,
    toggle_comment_dislike,
    get_comment_replies,
)
from apps.social.presentation.views.views_all_actions import (
    mark_private_chat_read,
    mark_group_chat_read,
    AchievementViewSet,
    AttachmentViewSet,
    PostAttachmentViewSet,
    EmailLogViewSet,
    FavoriteViewSet,
    ReportViewSet,
    RepostViewSet,
    UploadedFileViewSet,
    UserAchievementViewSet,
    AchievementAdminViewSet,
    get_chats_for_forward,
    forward_post_to_chat,
    get_extended_feed,
    get_post_comment_replies,
    get_franchise_discussions,
    GroupSearchView,
    get_hashtag_posts,
    search_hashtags,
    search_messages,
    reindex_messages,
    pin_post,
    unpin_post,
    report_post,
    add_bookmark,
    remove_bookmark,
    toggle_bookmark_view,
    get_bookmarks_folders,
    hide_post_from_feed,
    mark_post_not_interested,
    edit_post,
    get_user_posts,
    get_group_posts,
    hide_author_from_feed,
    get_hidden_posts,
    restore_hidden_post,
    get_bookmarked_posts,
    get_feed_statistics,
    get_popular_posts,
    get_user_notification_settings,
    update_user_notification_settings,
    report_comment,
    edit_comment,
    toggle_follow,
    toggle_post_like,
    toggle_post_dislike,
    get_post_likes,
    get_post_dislikers,
    create_repost,
    delete_repost,
    repost_post,
    unrepost_post,
    track_post_view,
    get_post_viewers,
    upload_file,
    get_online_users,
    pin_message,
    unpin_message,
    forward_message,
    get_pinned_messages,
    upload_attachment,
    BookmarkViewSet,
    SubscriptionViewSet,
    NotInterestedViewSet,
    ModerationReportViewSet,
    ReactionViewSet,
)
from apps.social.presentation.views.views_news import (
    NewsListView,
    NewsDetailView,
    NewsCreateView,
    NewsUpdateView,
    NewsDeleteView,
    register_news_view,
)

try:
    from .views.moderation_views import (
        get_reports,
        resolve_report,
    )
except ImportError:
    pass

try:
    from apps.social.application._discussion_views_patch import (
        get_anime_discussion_group,
        create_anime_discussion_group,
        join_anime_discussion_group,
        leave_anime_discussion_group,
        get_franchise_discussion_group,
        join_franchise_discussion_group,
    )
except ImportError:
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response

    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def get_anime_discussion_group(request, anime_id):
        from apps.social.infrastructure.models.social import GroupChat, ChatMember
        from apps.social.presentation.serializers.social_serializers import GroupChatSerializer

        try:
            from apps.anime.infrastructure.models.anime import Anime

            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({"error": "Аниме не найдено"}, status=404)

        try:
            chat = GroupChat.objects.get(anime_id=anime_id)
            serializer = GroupChatSerializer(chat, context={"request": request})
            return Response(serializer.data)
        except GroupChat.DoesNotExist:
            return Response({"error": "Чат не найден"}, status=404)

    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def create_anime_discussion_group(request, anime_id):
        from apps.social.infrastructure.models.social import GroupChat, ChatMember
        from apps.social.presentation.serializers.social_serializers import GroupChatSerializer

        try:
            from apps.anime.infrastructure.models.anime import Anime

            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({"error": "Аниме не найдено"}, status=404)

        if GroupChat.objects.filter(anime_id=anime_id).exists():
            return Response({"error": "Чат для этого аниме уже существует"}, status=400)

        chat = GroupChat.objects.create(
            name=anime.title_ru or anime.title_en,
            anime_id=anime_id,
            created_by=request.user,
            is_public=True,
            description=anime.description[:500] if anime.description else "",
            discussion_type="anime",
            folder_type="discussions",
        )
        ChatMember.objects.get_or_create(
            user=request.user, chat=chat, defaults={"is_admin": True}
        )
        serializer = GroupChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=201)

    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def join_anime_discussion_group(request, anime_id):
        from apps.social.infrastructure.models.social import GroupChat, ChatMember
        from apps.social.presentation.serializers.social_serializers import GroupChatSerializer

        try:
            from apps.anime.infrastructure.models.anime import Anime

            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({"error": "Аниме не найдено"}, status=404)

        try:
            chat = GroupChat.objects.get(anime_id=anime_id)
        except GroupChat.DoesNotExist:
            chat = GroupChat.objects.create(
                name=anime.title_ru or anime.title_en,
                anime_id=anime_id,
                created_by=request.user,
                is_public=True,
                description=(anime.description or "")[:500],
                discussion_type="anime",
                folder_type="discussions",
            )
            ChatMember.objects.create(user=request.user, chat=chat, is_admin=True)

        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            if chat.members.count() >= chat.max_members:
                return Response({"error": "Чат переполнен"}, status=400)
            ChatMember.objects.create(user=request.user, chat=chat)

        return Response(
            {
                "success": True,
                "chat_id": chat.id,
                "chat": GroupChatSerializer(chat, context={"request": request}).data,
            }
        )

    @api_view(["GET", "POST"])
    @permission_classes([IsAuthenticated])
    def get_franchise_discussion_group(request, franchise_id):
        from apps.social.infrastructure.models.social import GroupChat
        from apps.social.presentation.serializers.social_serializers import GroupChatSerializer

        try:
            chat = GroupChat.objects.get(franchise_id=franchise_id)
            serializer = GroupChatSerializer(chat, context={"request": request})
            return Response(serializer.data)
        except GroupChat.DoesNotExist:
            return Response({"error": "Чат не найден"}, status=404)

    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def join_franchise_discussion_group(request, franchise_id):
        from apps.social.infrastructure.models.social import GroupChat, ChatMember

        try:
            chat = GroupChat.objects.get(franchise_id=franchise_id)
        except GroupChat.DoesNotExist:
            return Response({"error": "Чат не найден"}, status=404)
        if ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({"message": "Вы уже участник", "chat_id": chat.id})
        ChatMember.objects.create(user=request.user, chat=chat)
        return Response({"success": True, "chat_id": chat.id})


from apps.social.presentation.views.views_chat import (
    init_franchise_discussion,
    global_chat_style,
    ChatCustomizationViewSet,
    ChatInviteLinkViewSet,
    join_chat_by_invite as join_invite_new,
    ChatBanViewSet,
    ChatRestrictionViewSet,
    ChatSlowModeViewSet,
    ChatJoinRequestViewSet,
    ChatTagViewSet,
    ChatTagAssignmentViewSet,
    AntiSpamRuleViewSet,
    ChatBackupViewSet,
    ScheduledMessageViewSet,
    ChatFolderViewSet,
    get_folder_chats,
    SecurityLogViewSet,
    get_chat_analytics,
    export_settings,
    import_settings,
    bulk_delete_messages,
    bulk_add_members,
    bulk_remove_members,
    pin_message_new,
    unpin_message_new,
    get_pinned_messages_new,
    check_message_spam,
    clear_chat_history,
    set_member_role,
    transfer_ownership,
    remove_member,
    ban_user,
    unban_user,
    get_banned_users,
    get_restricted_users,
    toggle_reaction as toggle_reaction_new,
    private_chat_user_settings,
    mute_private_chat,
    unmute_private_chat,
    block_user_in_private_chat,
    unblock_user_in_private_chat,
    delete_private_chat,
    group_member_settings,
    mute_group_chat,
    unmute_group_chat,
    archive_group_chat,
    archive_private_chat,
    get_group_notification_settings,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    from apps.users.presentation.serializers.users_serializers import UserSerializer

    data = UserSerializer(request.user, context={"request": request}).data
    data["avatar_url"] = request.user.avatar.url if request.user.avatar else None
    return Response(data)


router = DefaultRouter()
router.register(r"groups", GroupViewSet)
router.register(r"posts", PostViewSet)
from apps.social.presentation.views.post_uploads import PostUploadViewSet
router.register(r'post-uploads', PostUploadViewSet, basename='post-uploads')
router.register(r"feed", FeedViewSet, basename="feed")
router.register(r"bookmarks", BookmarkViewSet, basename="bookmark")
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"group-chats", GroupChatViewSet)
router.register(
    r"group-chats/(?P<chat_pk>\d+)/roles", ChatRoleViewSet, basename="chat-roles"
)
router.register(r"private-chats", PrivateChatViewSet)
router.register(r"follows", FollowViewSet, basename="follow")
router.register(r"reposts", RepostViewSet, basename="repost")
router.register(r"achievements", AchievementViewSet, basename="achievement")
router.register(
    r"user-achievements", UserAchievementViewSet, basename="user-achievement"
)
router.register(
    r"admin/achievements", AchievementAdminViewSet, basename="admin-achievement"
)
router.register(r"uploaded-files", UploadedFileViewSet, basename="uploaded-file")
router.register(r"favorites", FavoriteViewSet, basename="favorite")
router.register(r"reactions", ReactionViewSet, basename="reaction")
router.register(r"attachments", AttachmentViewSet, basename="attachment")
router.register(r"post-attachments", PostAttachmentViewSet, basename="post-attachment")
router.register(r"email-logs", EmailLogViewSet, basename="email-log")
router.register(r"chat-folders", ChatFolderViewSet, basename="chat-folder")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"not-interested", NotInterestedViewSet, basename="not-interested")
router.register(
    r"moderation/reports", ModerationReportViewSet, basename="moderation-report"
)

router.register(
    r"chat-customization", ChatCustomizationViewSet, basename="chat-customization"
)
router.register(
    r"chat-invite-links", ChatInviteLinkViewSet, basename="chat-invite-link"
)
router.register(r"chat-bans", ChatBanViewSet, basename="chat-ban")
router.register(r"chat-slow-modes", ChatSlowModeViewSet, basename="chat-slow-mode")
router.register(
    r"chat-restrictions", ChatRestrictionViewSet, basename="chat-restriction"
)
router.register(
    r"chat-join-requests", ChatJoinRequestViewSet, basename="chat-join-request"
)
router.register(r"chat-tags", ChatTagViewSet, basename="chat-tag")
router.register(r"chat-tag-assignments", ChatTagAssignmentViewSet, basename="chat-tag-assignment")
router.register(r"anti-spam-rules", AntiSpamRuleViewSet, basename="anti-spam-rule")
router.register(r"chat-backups", ChatBackupViewSet, basename="chat-backup")
router.register(
    r"scheduled-messages", ScheduledMessageViewSet, basename="scheduled-message"
)
router.register(r"security-logs", SecurityLogViewSet, basename="security-log")

from apps.social.presentation.views.views_support import SupportTicketViewSet

router.register(r"support", SupportTicketViewSet, basename="support")

from apps.social.presentation.views.conversation_views import (
    get_chat_detail, MessageListCreateView, MessageDetailView, edit_message,
    delete_message, mark_private_chat_read, mark_group_chat_read, mark_chat_read,
    search_messages, chat_events, get_unread_chats, toggle_reaction_new, message_reactions,
    pin_message, unpin_message, get_pinned_messages, forward_message, bulk_delete_messages, clear_chat_history, upload_attachment,
)

urlpatterns = [
    path("group-chats/<int:chat_id>/settings/", group_settings, name="group-chat-settings"),
    path("chat-media/<path:name>", chat_media, name="chat-private-media"),
    path("chats/<int:chat_id>/events/", chat_events, name="chat-events"),
    path("users/me/", get_current_user, name="current-user"),
    path("users/me/feed/", FeedViewSet.as_view({"get": "list"}), name="user-feed"),
    path(
        "feed/trending/", FeedViewSet.as_view({"get": "trending"}), name="feed-trending"
    ),
    path(
        "feed/followers/",
        FeedViewSet.as_view({"get": "followers"}),
        name="feed-followers",
    ),
    path(
        "feed/weighted/", FeedViewSet.as_view({"get": "weighted"}), name="feed-weighted"
    ),
    path("feed/hot/", FeedViewSet.as_view({"get": "hot"}), name="feed-hot"),
    path("feed/top/", FeedViewSet.as_view({"get": "top"}), name="feed-top"),
    path(
        "feed/matching-channels/",
        FeedViewSet.as_view({"get": "matching_channels"}),
        name="feed-matching-channels",
    ),
    path("feed/extended/", get_extended_feed, name="feed-extended"),
    path("feed/", get_extended_feed, name="feed"),
    path("chats/", CombinedChatsView.as_view(), name="combined-chats"),
    path(
        "chats/private/",
        PrivateChatViewSet.as_view({"post": "create"}),
        name="create-private-chat",
    ),
    path("chats/<int:pk>/", get_chat_detail, name="chat-detail"),
    path("chats/<int:pk>/settings/", get_chat_detail, name="chat-settings"),
    path(
        "chats/<int:chat_id>/messages/",
        MessageListCreateView.as_view(),
        name="chat-messages",
    ),
    path("messages/", MessageListCreateView.as_view(), name="messages-list-create"),
    path(
        "messages/<int:message_id>/", MessageDetailView.as_view(), name="message-detail"
    ),
    path(
        "messages/<int:message_id>/edit/",
        edit_message,
        name="message-edit",
    ),
    path(
        "messages/<int:message_id>/delete/",
        delete_message,
        name="message-delete",
    ),
    path(
        "messages/<int:message_id>/read/",
        mark_message_read,
        name="message-read",
    ),
    path(
        "private-chats/<int:chat_id>/settings/",
        private_chat_user_settings,
        name="private-chat-settings",
    ),
    path(
        "private-chats/<int:chat_id>/user-settings/",
        private_chat_user_settings,
        name="private-chat-user-settings",
    ),
    path(
        "private-chats/<int:chat_id>/mute/", mute_private_chat, name="mute-private-chat"
    ),
    path(
        "private-chats/<int:chat_id>/unmute/",
        unmute_private_chat,
        name="unmute-private-chat",
    ),
    path(
        "private-chats/<int:chat_id>/block/",
        block_user_in_private_chat,
        name="block-private-chat",
    ),
    path(
        "private-chats/<int:chat_id>/unblock/",
        unblock_user_in_private_chat,
        name="unblock-private-chat",
    ),
    path(
        "private-chats/<int:chat_id>/delete/",
        delete_private_chat,
        name="delete-private-chat",
    ),
    path(
        "private-chats/<int:chat_id>/mark_as_read/",
        mark_private_chat_read,
        name="mark-private-chat-read",
    ),
    path(
        "private-chats/<int:chat_id>/clear_history/",
        clear_chat_history,
        name="private-chat-clear-history",
    ),
    path(
        "group-chats/<int:chat_id>/settings/",
        group_member_settings,
        name="group-chat-settings",
    ),
    path(
        "group-chats/<int:chat_id>/member-settings/",
        group_member_settings,
        name="group-member-settings",
    ),
    path("group-chats/<int:chat_id>/mute/", mute_group_chat, name="mute-group-chat"),
    path(
        "group-chats/<int:chat_id>/unmute/", unmute_group_chat, name="unmute-group-chat"
    ),
    path(
        "group-chats/<int:chat_id>/notification-settings/",
        get_group_notification_settings,
        name="group-notification-settings",
    ),
    path(
        "group-chats/<int:chat_id>/archive/",
        archive_group_chat,
        name="archive-group-chat",
    ),
    path(
        "group-chats/<int:chat_id>/mark_as_read/",
        mark_group_chat_read,
        name="mark-group-chat-read",
    ),
    path(
        "private-chats/<int:chat_id>/archive/",
        archive_private_chat,
        name="archive-private-chat",
    ),
    path(
        "chat-settings/group/<int:chat_id>/wallpaper/",
        ChatCustomizationViewSet.as_view({"get": "get_wallpaper"}),
        {"chat_type": "group"},
        name="group-wallpaper",
    ),
    path(
        "chat-settings/group/<int:chat_id>/wallpaper/set/",
        ChatCustomizationViewSet.as_view(
            {"put": "set_wallpaper", "post": "set_wallpaper"}
        ),
        {"chat_type": "group"},
        name="set-group-wallpaper",
    ),
    path(
        "chat-settings/group/<int:chat_id>/wallpaper/reset/",
        ChatCustomizationViewSet.as_view({"delete": "reset_wallpaper"}),
        {"chat_type": "group"},
        name="reset-group-wallpaper",
    ),
    path(
        "chat-settings/group/<int:chat_id>/wallpaper/preset/",
        ChatCustomizationViewSet.as_view({"post": "apply_wallpaper_preset"}),
        {"chat_type": "group"},
        name="group-wallpaper-preset",
    ),
    path(
        "chat-settings/private/<int:chat_id>/wallpaper/",
        ChatCustomizationViewSet.as_view({"get": "get_wallpaper"}),
        {"chat_type": "private"},
        name="private-wallpaper",
    ),
    path(
        "chat-settings/private/<int:chat_id>/wallpaper/set/",
        ChatCustomizationViewSet.as_view(
            {"put": "set_wallpaper", "post": "set_wallpaper"}
        ),
        {"chat_type": "private"},
        name="set-private-wallpaper",
    ),
    path(
        "chat-settings/private/<int:chat_id>/wallpaper/reset/",
        ChatCustomizationViewSet.as_view({"delete": "reset_wallpaper"}),
        {"chat_type": "private"},
        name="reset-private-wallpaper",
    ),
    path(
        "chat-settings/private/<int:chat_id>/wallpaper/preset/",
        ChatCustomizationViewSet.as_view({"post": "apply_wallpaper_preset"}),
        {"chat_type": "private"},
        name="private-wallpaper-preset",
    ),
    path(
        "chat-settings/group/<int:chat_id>/theme/",
        ChatCustomizationViewSet.as_view({"get": "get_theme"}),
        {"chat_type": "group"},
        name="group-theme",
    ),
    path(
        "chat-settings/group/<int:chat_id>/theme/set/",
        ChatCustomizationViewSet.as_view({"put": "set_theme", "post": "set_theme"}),
        {"chat_type": "group"},
        name="set-group-theme",
    ),
    path(
        "chat-settings/group/<int:chat_id>/theme/preset/",
        ChatCustomizationViewSet.as_view({"post": "apply_theme_preset"}),
        {"chat_type": "group"},
        name="group-theme-preset",
    ),
    path(
        "chat-settings/group/<int:chat_id>/theme/reset/",
        ChatCustomizationViewSet.as_view({"delete": "reset_theme"}),
        {"chat_type": "group"},
        name="reset-group-theme",
    ),
    path(
        "chat-settings/private/<int:chat_id>/theme/",
        ChatCustomizationViewSet.as_view({"get": "get_theme"}),
        {"chat_type": "private"},
        name="private-theme",
    ),
    path(
        "chat-settings/private/<int:chat_id>/theme/set/",
        ChatCustomizationViewSet.as_view({"put": "set_theme", "post": "set_theme"}),
        {"chat_type": "private"},
        name="set-private-theme",
    ),
    path(
        "chat-settings/private/<int:chat_id>/theme/preset/",
        ChatCustomizationViewSet.as_view({"post": "apply_theme_preset"}),
        {"chat_type": "private"},
        name="private-theme-preset",
    ),
    path(
        "chat-settings/private/<int:chat_id>/theme/reset/",
        ChatCustomizationViewSet.as_view({"delete": "reset_theme"}),
        {"chat_type": "private"},
        name="reset-private-theme",
    ),
    path(
        "chat-settings/group/<int:chat_id>/all/",
        ChatCustomizationViewSet.as_view({"get": "get_all_settings"}),
        {"chat_type": "group"},
        name="group-all-settings",
    ),
    path(
        "chat-settings/private/<int:chat_id>/all/",
        ChatCustomizationViewSet.as_view({"get": "get_all_settings"}),
        {"chat_type": "private"},
        name="private-all-settings",
    ),
    path(
        "chat-settings/group/<int:chat_id>/bulk-update/",
        ChatCustomizationViewSet.as_view({"post": "bulk_update_settings"}),
        {"chat_type": "group"},
        name="group-bulk-settings",
    ),
    path(
        "chat-settings/private/<int:chat_id>/bulk-update/",
        ChatCustomizationViewSet.as_view({"post": "bulk_update_settings"}),
        {"chat_type": "private"},
        name="private-bulk-settings",
    ),
    path(
        "chat-settings/group/<int:chat_id>/css-vars/",
        ChatCustomizationViewSet.as_view({"get": "get_css_vars"}),
        {"chat_type": "group"},
        name="group-css-vars",
    ),
    path(
        "chat-settings/private/<int:chat_id>/css-vars/",
        ChatCustomizationViewSet.as_view({"get": "get_css_vars"}),
        {"chat_type": "private"},
        name="private-css-vars",
    ),
    path(
        "chat-settings/wallpapers/presets/",
        ChatCustomizationViewSet.as_view({"get": "wallpaper_presets"}),
        name="wallpaper-presets",
    ),
    path(
        "chat-settings/themes/presets/",
        ChatCustomizationViewSet.as_view({"get": "theme_presets"}),
        name="theme-presets",
    ),
    path("comments/", CommentListCreateView.as_view(), name="comment-list-create"),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
    path(
        "posts/<int:post_pk>/comments/",
        PostCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="post-comments",
    ),
    path(
        "posts/<int:post_pk>/comments/<int:pk>/",
        PostCommentViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="post-comment-detail",
    ),
    path(
        "comments/<int:comment_id>/like/",
        toggle_comment_like,
        name="toggle-comment-like",
    ),
    path(
        "comments/<int:comment_id>/dislike/",
        toggle_comment_dislike,
        name="toggle-comment-dislike",
    ),
    path(
        "comments/<int:comment_id>/replies/",
        get_comment_replies,
        name="get-comment-replies",
    ),
    path("comments/<int:comment_id>/report/", report_comment, name="report-comment"),
    path("comments/<int:comment_id>/edit/", edit_comment, name="edit-comment"),
    path(
        "posts/comments/<int:comment_id>/replies/",
        get_post_comment_replies,
        name="get-post-comment-replies",
    ),
    path("follow/toggle/<int:user_id>/", toggle_follow, name="toggle-follow"),
    path(
        "subscriptions/toggle/<int:user_id>/", toggle_follow, name="toggle-subscription"
    ),
    path("posts/<int:post_id>/like/", toggle_post_like, name="toggle-post-like"),
    path(
        "posts/<int:post_id>/dislike/", toggle_post_dislike, name="toggle-post-dislike"
    ),
    path("posts/<int:post_id>/likes/", get_post_likes, name="get-post-likes"),
    path("posts/<int:post_id>/likers/", get_post_likers, name="get-post-likers"),
    path(
        "posts/<int:post_id>/dislikers/", get_post_dislikers, name="get-post-dislikers"
    ),
    path("posts/<int:post_id>/repost/", create_repost, name="create-repost"),
    path("posts/<int:post_id>/repost/delete/", delete_repost, name="delete-repost"),
    path("posts/<int:post_id>/repost/action/", repost_post, name="repost-post"),
    path("posts/<int:post_id>/repost/remove/", unrepost_post, name="unrepost-post"),
    path("posts/<int:post_id>/view/", track_post_view, name="track-post-view"),
    path("posts/<int:post_id>/viewers/", get_post_viewers, name="get-post-viewers"),
    path("files/upload/", upload_file, name="upload-file"),
    path("users/online/", get_online_users, name="get-online-users"),
    path(
        "groups/search/", GroupSearchView.as_view({"get": "list"}), name="group-search"
    ),
    path("hashtags/<str:tag_name>/", get_hashtag_posts, name="get-hashtag-posts"),
    path("hashtags/search/", search_hashtags, name="search-hashtags"),
    path("messages/search/", search_messages, name="search-messages"),
    path("messages/reindex/", reindex_messages, name="reindex-messages"),
    path(
        "chat-invites/join/<str:token>/",
        join_invite_new,
        name="join-chat-by-invite",
    ),
    path(
        "invite-links/join/<str:token>/",
        join_invite_new,
        name="join-chat-by-invite-new",
    ),
    path(
        "group-chats/<int:chat_id>/invite-links/",
        ChatInviteLinkViewSet.as_view({"get": "list", "post": "create"}),
        name="chat-invite-links",
    ),
    path(
        "messages/<int:message_id>/reaction/toggle/",
        toggle_reaction_new,
        name="toggle-reaction",
    ),
    path(
        "messages/<int:message_id>/reaction/new/",
        toggle_reaction_new,
        name="toggle-reaction-new",
    ),
    path(
        "messages/<int:message_id>/reactions/",
        message_reactions,
        name="message-reactions",
    ),
    path(
        "messages/<int:message_id>/attachments/upload/",
        upload_attachment,
        name="upload-attachment",
    ),
    path("messages/<int:message_id>/pin/", pin_message, name="pin-message"),
    path("messages/<int:message_id>/unpin/", unpin_message, name="unpin-message"),
    path("messages/<int:message_id>/forward/", forward_message, name="forward-message"),
    path(
        "chats/<int:chat_id>/pinned-messages/",
        get_pinned_messages,
        name="get-pinned-messages",
    ),
    path("messages/<int:message_id>/pin-v2/", pin_message, name="pin-message-v2"),
    path(
        "messages/<int:message_id>/unpin-v2/",
        unpin_message,
        name="unpin-message-v2",
    ),
    path(
        "chats/<int:chat_id>/pinned-messages-v2/",
        get_pinned_messages,
        name="get-pinned-messages-v2",
    ),
    path("chats/unread-count/", get_unread_count, name="get-unread-count"),
    path("chats/unread/", get_unread_chats, name="get-unread-chats"),
    path("chats/<int:chat_id>/mark-read/", mark_chat_read, name="mark-chat-read"),
    path(
        "posts/<int:pk>/public/",
        PostViewSet.as_view({"get": "public_retrieve"}),
        name="post-detail-public",
    ),
    path("posts/<int:post_id>/pin/", pin_post, name="pin-post"),
    path("posts/<int:post_id>/unpin/", unpin_post, name="unpin-post"),
    path("posts/<int:post_id>/report/", report_post, name="report-post"),
    path("posts/<int:post_id>/bookmark/", add_bookmark, name="add-bookmark"),
    path(
        "posts/<int:post_id>/bookmark/remove/", remove_bookmark, name="remove-bookmark"
    ),
    path("bookmarks/toggle/", toggle_bookmark_view, name="toggle-bookmark"),
    path("bookmarks/folders/", get_bookmarks_folders, name="bookmarks-folders"),
    path("posts/<int:post_id>/hide/", hide_post_from_feed, name="hide-post"),
    path(
        "posts/<int:post_id>/not-interested/",
        mark_post_not_interested,
        name="not-interested",
    ),
    path("posts/<int:post_id>/edit/", edit_post, name="edit-post"),
    path("users/<int:user_id>/posts/", get_user_posts, name="user-posts"),
    path("groups/<int:group_id>/posts/", get_group_posts, name="group-posts"),
    path("users/<int:user_id>/hide/", hide_author_from_feed, name="hide-author"),
    path("hidden-posts/", get_hidden_posts, name="hidden-posts"),
    path(
        "hidden-posts/<int:post_id>/restore/",
        restore_hidden_post,
        name="restore-hidden-post",
    ),
    path("bookmarks/posts/", get_bookmarked_posts, name="bookmarked-posts"),
    path("feed/statistics/", get_feed_statistics, name="feed-statistics"),
    path("feed/popular/", get_popular_posts, name="popular-posts"),
    path(
        "notifications/settings/",
        get_user_notification_settings,
        name="notification-settings",
    ),
    path(
        "notifications/settings/update/",
        update_user_notification_settings,
        name="update-notification-settings",
    ),
    path(
        "not-interested/user/<int:user_id>/",
        mark_post_not_interested,
        name="not-interested-user",
    ),
    path(
        "group-chats/<int:chat_id>/members/<int:user_id>/role/",
        set_member_role,
        name="set-member-role",
    ),
    path(
        "group-chats/<int:chat_id>/transfer-ownership/",
        transfer_ownership,
        name="transfer-ownership",
    ),
    path(
        "group-chats/<int:chat_id>/remove_member/",
        remove_member,
        name="remove-member",
    ),
    path(
        "moderation/reports/",
        get_reports,
        name="get-reports",
    ),
    path(
        "moderation/reports/<int:report_id>/resolve/",
        resolve_report,
        name="resolve-report",
    ),
    path(
        "group-chats/<int:chat_id>/banned-users/",
        get_banned_users,
        name="get-banned-users",
    ),
    path(
        "group-chats/<int:chat_id>/restricted-users/",
        get_restricted_users,
        name="get-restricted-users",
    ),
    path(
        "group-chats/<int:chat_id>/join-requests/",
        ChatJoinRequestViewSet.as_view({"get": "list", "post": "create"}),
        name="chat-join-requests",
    ),
    path(
        "group-chats/<int:chat_id>/join-requests/<int:pk>/approve/",
        ChatJoinRequestViewSet.as_view({"post": "approve"}),
        name="approve-join-request",
    ),
    path(
        "group-chats/<int:chat_id>/join-requests/<int:pk>/reject/",
        ChatJoinRequestViewSet.as_view({"post": "reject"}),
        name="reject-join-request",
    ),
    path(
        "group-chats/<int:chat_id>/anti-spam-rules/",
        AntiSpamRuleViewSet.as_view({"get": "list", "post": "create"}),
        name="anti-spam-rules",
    ),
    path(
        "group-chats/<int:chat_id>/check-spam/",
        check_message_spam,
        name="check-message-spam",
    ),
    path(
        "group-chats/<int:chat_id>/backups/",
        ChatBackupViewSet.as_view({"get": "list", "post": "create"}),
        name="chat-backups",
    ),
    path("chat-folders/<int:folder_id>/chats/", get_folder_chats, name="folder-chats"),
    path(
        "chat-folders/reorder/",
        ChatFolderViewSet.as_view({"post": "reorder", "patch": "reorder"}),
        name="reorder-folders",
    ),
    path(
        "chat-folders/<int:pk>/add-chat/",
        ChatFolderViewSet.as_view({"post": "add_chat"}),
        name="add-chat-to-folder",
    ),
    path(
        "chat-folders/<int:pk>/remove-chat/",
        ChatFolderViewSet.as_view({"post": "remove_chat"}),
        name="remove-chat-from-folder",
    ),
    path(
        "group-chats/<int:chat_id>/analytics/",
        get_chat_analytics,
        name="chat-analytics",
    ),
    path("settings/export/", export_settings, name="export-settings"),
    path("settings/import/", import_settings, name="import-settings"),
    path(
        "group-chats/<int:chat_id>/messages/bulk-delete/",
        bulk_delete_messages,
        name="bulk-delete-messages",
    ),
    path(
        "group-chats/<int:chat_id>/members/bulk-add/",
        bulk_add_members,
        name="bulk-add-members",
    ),
    path(
        "group-chats/<int:chat_id>/members/bulk-remove/",
        bulk_remove_members,
        name="bulk-remove-members",
    ),
    path(
        "group-chats/<int:chat_id>/ban_user/",
        ban_user,
        name="ban-user",
    ),
    path(
        "group-chats/<int:chat_id>/unban_user/",
        unban_user,
        name="unban-user",
    ),
    path(
        "chats/<int:chat_id>/clear-history/",
        clear_chat_history,
        name="clear-chat-history",
    ),
    path("chats/for-forward/", get_chats_for_forward, name="chats-for-forward"),
    path("chats/<int:chat_id>/forward/", forward_post_to_chat, name="forward-post"),
    path("chats/forward/", forward_post_to_chat, name="forward-post-no-id"),
    path(
        "anime/<int:anime_id>/discussion-group/",
        get_anime_discussion_group,
        name="anime-discussion-group",
    ),
    path(
        "anime/<int:anime_id>/discussion-group/create/",
        create_anime_discussion_group,
        name="anime-discussion-group-create",
    ),
    path(
        "anime/<int:anime_id>/discussion-group/join/",
        join_anime_discussion_group,
        name="anime-discussion-group-join",
    ),
    path(
        "franchise/<int:franchise_id>/discussion/",
        get_franchise_discussion_group,
        name="franchise-discussion",
    ),
    path(
        "franchise/<int:franchise_id>/discussion/join/",
        join_franchise_discussion_group,
        name="franchise-discussion-join",
    ),
    path(
        "franchise-discussion/init/",
        init_franchise_discussion,
        name="franchise-discussion-init",
    ),
    path(
        "franchise-discussion/list/",
        get_franchise_discussions,
        name="franchise-discussion-list",
    ),
    path(
        "anime/<int:anime_id>/discussion-group/leave/",
        leave_anime_discussion_group,
        name="anime-discussion-leave",
    ),
    path("chat-settings/global/", global_chat_style, name="global-chat-style"),
    path("news/", NewsListView.as_view(), name="news-list"),
    path("news/<int:pk>/", NewsDetailView.as_view(), name="news-detail"),
    path("news/create/", NewsCreateView.as_view(), name="news-create"),
    path("news/<int:pk>/update/", NewsUpdateView.as_view(), name="news-update"),
    path("news/<int:pk>/delete/", NewsDeleteView.as_view(), name="news-delete"),
    path("news/<int:pk>/view/", register_news_view, name="news-view"),
] + router.urls
