import apiClient from "./client";
import type { Excerpt } from "./excerpts";

export type PostId = string | number;

export interface PostAttachmentItem {
  id: PostId;
  content_type: "anime" | "playlist" | "shorts" | "excerpt" | "unavailable";
  excerpt_data?: Excerpt | null;
  object_id: number;
  anime_data?: AnimeCard | null;
  playlist_data?: PlaylistCard | null;
  shorts_data?: ReactorCard | null;
}

export interface FeedPost {
  id: PostId;
  version?: number;
  public_id?: string;
  processing?: boolean;
  processing_media?: MediaFile[];
  author: number;
  author_username: string;
  author_display_name: string | null;
  author_avatar: string | null;
  title: string;
  post_type:
    "text" | "image" | "video" | "playlist" | "anime" | "repost" | "system";
  status: "published" | "draft" | "deleted" | "moderated" | "processing" | "failed";
  visibility: "public" | "followers" | "friends" | "private";
  text: string;
  image_url: string | null;
  image_file: string | null;
  video_url: string | null;
  video_file: string | null;
  is_following: boolean;
  anime: AnimeCard | null;
  anime_rating: number | null;
  playlist: PlaylistCard | null;
  reactor_post: ReactorCard | null;
  group: GroupCard | null;
  original_post: FeedPost | null;
  repost_comment: string;
  likes_count: number;
  dislikes_count: number;
  comments_count: number;
  reposts_count: number;
  views_count: number;
  shares_count: number;
  is_pinned: boolean;
  is_deleted: boolean;
  is_spoiler: boolean;
  spoiler_for?:
    | {
        id: PostId;
        title_ru?: string;
        title_en?: string;
      }
    | string
    | null;
  spoiler_description?: string | null;
  allow_comments: boolean;
  created_at: string;
  updated_at: string;
  edited_at: string | null;
  published_at: string | null;
  media_url?: string | null;
  media_files: MediaFile[];
  attachments_data?: PostAttachmentItem[];
  hashtags: string[];
  is_liked: boolean;
  is_disliked: boolean;
  is_bookmarked: boolean;
  is_owner?: boolean;
  can_edit: boolean;
  can_delete: boolean;
  system_type?: string | null;
  playlist_title?: string | null;
  anime_title?: string | null;
  original_post_data?: { author_username: string; text: string } | null;
  is_favorited?: boolean;
}

export interface MediaFile {
  id: PostId;
  media_type: "image" | "video";
  url: string | null;
  file_url: string | null;
  thumbnail?: string | null;
  thumbnail_url?: string | null;
  caption?: string | null;
  order: number;
  width?: number;
  height?: number;
  duration?: number;
  file_size?: number;
  processing_state?: 'queued' | 'processing' | 'ready' | 'failed';
  processing_progress?: number;
  processing_error?: string;
  upload_id?: string;
  sources?: { quality: string; url: string }[];
}

export interface AnimeCard {
  id: number;
  title_ru: string;
  title_en?: string;
  year?: number;
  description?: string;
  overview?: string;
  poster_url?: string;
  poster?: string | null;
  rating?: number;
  slug?: string;
}

export interface PlaylistCard {
  id: number | string;
  title: string;
  name?: string;
  anime_count: number;
  items_count?: number;
  description?: string;
  poster_url?: string | null;
  cover_image?: string | null;
  anime?: (AnimeCard & { poster?: string | null })[];
}

export interface ReactorCard {
  id: number;
  title?: string;
  video_url: string;
  duration?: number;
  likes_count: number;
  comments_count: number;
  user?: { username: string };
}

export interface GroupCard {
  id: number;
  name: string;
  slug: string;
}

export interface PostComment {
  id: PostId;
  post: PostId;
  author: number;
  author_username: string;
  author_display_name: string | null;
  author_avatar: string | null;
  parent: PostId | null;
  parent_id: PostId | null;
  parent_username?: string;
  content: string;
  is_edited: boolean;
  is_deleted: boolean;
  likes_count: number;
  dislikes_count: number;
  replies_count: number;
  replies?: PostComment[];
  level: number;
  created_at: string;
  updated_at: string;
  is_liked: boolean;
  is_disliked: boolean;
}

export interface FeedPage {
  results: FeedPost[];
  count: number;
  next: number | null;
  previous: number | null;
}

export interface MatchingChannel {
  user_id: number;
  username: string;
  display_name: string;
  avatar: string | null;
  posts_count: number;
  followers_count: number;
  is_following: boolean;
  match_score: number;
  match_reasons: string[];
}

export interface MatchingChannelsResponse {
  results: MatchingChannel[];
  count: number;
}

export const feedApi = {
  getWeightedFeed: (page = 1, pageSize = 20) =>
    apiClient.get<FeedPage>("/social/feed/weighted/", {
      params: { page, page_size: pageSize },
    }),

  getFollowersFeed: (page = 1, pageSize = 20) =>
    apiClient.get<FeedPage>("/social/feed/followers/", {
      params: { page, page_size: pageSize },
    }),

  getHotFeed: (hours = 24, limit = 20) =>
    apiClient.get<FeedPost[]>("/social/feed/hot/", {
      params: { hours, limit },
    }),

  getTopFeed: (days = 7, limit = 20) =>
    apiClient.get<FeedPost[]>("/social/feed/top/", { params: { days, limit } }),

  getTrendingFeed: (hours = 6, limit = 20) =>
    apiClient.get<FeedPost[]>("/social/feed/trending/", {
      params: { hours, limit },
    }),

  getPopularFeed: (page = 1, pageSize = 20, period = "week") =>
    apiClient.get<FeedPage>("/social/feed/popular/", {
      params: { page, page_size: pageSize, period },
    }),

  getPersonalizedTrending: (period: "24h" | "7d" | "30d" = "24h", limit = 20) =>
    apiClient.get<FeedPost[]>("/social/feed/personalized-trending/", {
      params: { period, limit },
    }),

  getMatchingChannels: (limit = 5) =>
    apiClient.get<MatchingChannelsResponse>("/social/feed/matching-channels/", {
      params: { limit },
    }),
};

export const postsApi = {
  getPost: (id: PostId) => apiClient.get<FeedPost>(`/social/posts/${id}/`),

  getPosts: (params?: {
    author?: number;
    group?: number;
    anime?: number;
    page?: number;
  }) => apiClient.get<FeedPage>("/social/posts/", { params }),

  createPost: (data: FormData | Record<string, unknown>) => {
    const isFormData = data instanceof FormData;
    return apiClient.post<FeedPost>("/social/posts/", data, {
      headers: isFormData ? {} : {},
    });
  },

  updatePost: (id: PostId, data: Partial<FeedPost>) =>
    apiClient.patch<FeedPost>(`/social/posts/${id}/`, data),

  deletePost: (id: PostId) => apiClient.delete(`/social/posts/${id}/`),

  likePost: (id: PostId) =>
    apiClient.post<{
      liked: boolean;
      likes_count: number;
      dislikes_count?: number;
    }>(`/social/posts/${id}/like/`),

  dislikePost: (id: PostId) =>
    apiClient.post<{
      disliked: boolean;
      dislikes_count: number;
      likes_count?: number;
    }>(`/social/posts/${id}/dislike/`),

  repostPost: (
    id: PostId,
    data?: {
      comment?: string;
      destination?: "feed" | "group" | "chat";
      target_id?: number;
      chat_id?: number;
      message?: string;
    },
  ) => apiClient.post(`/social/posts/${id}/repost/action/`, data || {}),

  unrepostPost: (id: PostId) =>
    apiClient.post(`/social/posts/${id}/repost/remove/`),

  editPost: (
    id: PostId,
    data: {
      text?: string;
      title?: string;
      visibility?: string;
      allow_comments?: boolean;
      is_spoiler?: boolean;
    },
  ) => apiClient.put(`/social/posts/${id}/edit/`, data),

  bookmarkPost: (id: PostId) => apiClient.post(`/social/posts/${id}/bookmark/`),

  removeBookmark: (id: PostId) =>
    apiClient.post(`/social/posts/${id}/bookmark/remove/`),

  toggleBookmark: (postId: PostId) =>
    apiClient.post("/social/bookmarks/toggle/", { post_id: postId }),

  viewPost: (id: PostId) => apiClient.post(`/social/posts/${id}/view/`),

  pinPost: (id: PostId) => apiClient.post(`/social/posts/${id}/pin/`),

  unpinPost: (id: PostId) => apiClient.post(`/social/posts/${id}/unpin/`),

  reportPost: (id: PostId, reason: string, comment?: string) =>
    apiClient.post("/social/reports/", {
      content_type: "post",
      content_id: id,
      reason,
      comment,
    }),

  hidePost: (id: PostId) => apiClient.post(`/social/posts/${id}/hide/`),

  notInterestedPost: (id: PostId) =>
    apiClient.post(`/social/posts/${id}/not-interested/`),

  getLikers: (id: PostId) => apiClient.get(`/social/posts/${id}/likers/`),

  getUserPosts: (userId: number, page = 1) =>
    apiClient.get<FeedPage>(`/social/users/${userId}/posts/`, {
      params: { page },
    }),
};

export const commentsApi = {
  getComments: (postId: PostId, page = 1) =>
    apiClient.get<PostComment[]>(`/social/posts/${postId}/comments/`, {
      params: { page, sort: "tree" },
    }),

  getCommentsTree: (postId: PostId, page = 1) =>
    apiClient.get<PostComment[]>(`/social/posts/${postId}/comments/`, {
      params: { sort: "tree", page_size: 100, page },
    }),

  createComment: (postId: PostId, content: string, parentId?: PostId, clientId: string = crypto.randomUUID()) =>
    apiClient.post<PostComment>(`/social/posts/${postId}/comments/`, {
      content,
      parent: parentId || null,
      client_comment_id: clientId,
    }),

  updateComment: (postId: PostId, commentId: PostId, content: string) =>
    apiClient.put<PostComment>(
      `/social/posts/${postId}/comments/${commentId}/`,
      { content },
    ),

  deleteComment: (postId: PostId, commentId: PostId) =>
    apiClient.delete(`/social/posts/${postId}/comments/${commentId}/`),

  likeComment: (commentId: PostId) =>
    apiClient.post<{ liked: boolean; likes_count: number; dislikes_count: number }>(
      `/social/comments/${commentId}/like/`,
    ),

  dislikeComment: (commentId: PostId) =>
    apiClient.post<{ disliked: boolean; likes_count: number; dislikes_count: number }>(
      `/social/comments/${commentId}/dislike/`,
    ),

  reportComment: (commentId: PostId, reason: string, comment = "") =>
    apiClient.post("/social/reports/", {
      content_type: "comment",
      content_id: commentId,
      reason,
      comment,
    }),
};

export interface SubscriptionUser {
  id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  avatar?: string | null;
  followers_count: number;
  is_online: boolean;
  followed_at: string;
}

export interface NotInterestedUser {
  id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  avatar?: string | null;
  hidden_at: string;
  reason?: string;
}

export interface HiddenPost {
  id: PostId;
  post_id: PostId;
  post_preview: string;
  hidden_at: string;
}

export interface ReportItem {
  id: number;
  reporter: {
    id: number;
    username: string;
    nickname?: string | null;
    url?: string;
    display_name?: string | null;
  };
  reporter_username?: string;
  content_type: "post" | "comment" | "user";
  content_id: PostId;
  reason: string;
  reason_display?: string;
  comment: string;
  status: "pending" | "resolved" | "rejected" | string;
  status_display?: string;
  resolved_by?: {
    id: number;
    username: string;
  } | null;
  resolved_at?: string | null;
  created_at: string;
  description?: string;
  content_preview?: {
    title?: string;
    text?: string;
    author?: { id?: number | null; username: string; nickname?: string | null };
    url?: string | null;
    available?: boolean;
    media?: Array<{ id?: number; type: string; url?: string | null; caption?: string }>;
  };
  moderation_comment?: string;
}

export const subscriptionsApi = {
  getSubscriptions: (page = 1, search?: string, sort = "date") =>
    apiClient.get<{
      results: SubscriptionUser[];
      count: number;
      next: number | null;
    }>("/social/subscriptions/", {
      params: { page, search, sort },
    }),

  unfollow: (userId: number) =>
    apiClient.delete<{ success: boolean; message: string }>(
      `/social/subscriptions/${userId}/unfollow/`,
    ),

  getNotInterested: (page = 1, search?: string) =>
    apiClient.get<{
      results: NotInterestedUser[];
      count: number;
      next: number | null;
    }>("/social/not-interested/", {
      params: { page, search },
    }),

  getHiddenPosts: (page = 1) =>
    apiClient.get<{
      results: HiddenPost[];
      count: number;
      next: number | null;
    }>("/social/hidden-posts/", {
      params: { page },
    }),

  restoreHiddenPost: (postId: PostId) =>
    apiClient.delete<{ success: boolean; message: string }>(
      `/social/hidden-posts/${postId}/restore/`,
    ),

  removeNotInterested: (userId: number) =>
    apiClient.delete<{ hidden: boolean; message: string }>(
      `/social/not-interested/${userId}/`,
    ),

  addNotInterested: (userId: number) =>
    apiClient.post<{ success: boolean; message: string }>(
      `/social/users/${userId}/hide/`,
    ),

  getReports: (params?: {
    status?: string;
    content_type?: string;
    reason?: string;
    page?: number;
    per_page?: number;
  }) =>
    apiClient.get<{
      results: ReportItem[];
      count: number;
      page: number;
      per_page: number;
      total_pages: number;
      next: number | null;
    }>("/social/moderation/reports/", { params }),

  resolveReport: (id: number, action: string, comment?: string) =>
    apiClient.post<{
      success: boolean;
      message: string;
      report: {
        id: number;
        status: string;
        resolved_by: string;
        resolved_at: string;
      };
    }>(`/social/moderation/reports/${id}/resolve/`, {
      status: "resolved",
      action,
      moderator_comment: comment,
    }),

  rejectReport: (id: number, comment?: string) =>
    apiClient.post<{
      success: boolean;
      message: string;
      report: {
        id: number;
        status: string;
        resolved_by: string;
        resolved_at: string;
      };
    }>(`/social/moderation/reports/${id}/resolve/`, {
      status: "rejected",
      action: "none",
      moderator_comment: comment || "Нарушение не подтверждено.",
    }),
};

export const bookmarksApi = {
  getPosts: (page = 1) =>
    apiClient.get<{ results: FeedPost[]; count: number; next: number | null }>(
      "/social/bookmarks/posts/",
      {
        params: { page },
      },
    ),
};

export interface ForwardChat {
  id: number;
  type: "private" | "group";
  name: string;
  avatar: string | null;
  is_online?: boolean;
  members_count?: number;
}

export const chatsApi = {
  getChatsForForward: (search?: string) =>
    apiClient.get<ForwardChat[]>("/social/chats/for-forward/", {
      params: { search },
    }),

  forwardPost: (chatId: number, postId: PostId, message?: string) =>
    apiClient.post<{ success: boolean; message_id: number; chat_id: number }>(
      "/social/chats/forward/",
      {
        chat_id: chatId,
        post_id: postId,
        message,
      },
    ),
};

export interface ExtendedFeedParams {
  page?: number;
  page_size?: number;
  sort?: "new" | "old" | "best" | "discussed";
  anime_id?: number;
  my_posts?: boolean;
  subscriptions?: boolean;
  groups?: boolean;
  tags?: string[];
  date_range?: "all" | "month" | "week" | "day";
}

export const extendedFeedApi = {
  getFeed: (params: ExtendedFeedParams = {}) =>
    apiClient.get<{
      results: FeedPost[];
      count: number;
      next: number | null;
      previous: number | null;
    }>("/social/feed/extended/", { params }),
};

export const followsApi = {
  toggleFollow: (userId: number) =>
    apiClient.post<{ following: boolean; message: string }>(
      `/social/follow/toggle/${userId}/`,
    ),

  getFollowers: (userId: number, page = 1) =>
    apiClient.get(`/social/follows/`, { params: { following: userId, page } }),

  getFollowing: (userId: number, page = 1) =>
    apiClient.get(`/social/follows/`, { params: { follower: userId, page } }),
};
