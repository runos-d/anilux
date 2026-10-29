import apiClient, { isRequestCancelled, getMediaUrl as resolveMediaUrl } from "./client";
import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "@/stores/auth";

async function readGroupChats() {
  const data = await queryClient.fetchQuery({
    queryKey: ["read", String(useAuthStore().user?.id ?? "guest"), "group-chats"],
    queryFn: async ({ signal }) => (await apiClient.get("/social/group-chats/", { signal })).data,
    staleTime: 60_000,
  });
  return (data.results || data) as GroupChat[];
}
import type {
  ChatFolder,
  CreateFolderData,
  UpdateFolderData,
  FolderPreview,
  Chat,
  GroupChat,
} from "@/types/chat";

const getMediaUrl = (path: string | null | undefined): string => resolveMediaUrl(path) || "";

export const chatFoldersApi = {
  async getAll(): Promise<ChatFolder[]> {
    try {
      const response = await apiClient.get("/social/chat-folders/");
      return response.data;
    } catch {
      return [];
    }
  },

  async create(data: CreateFolderData): Promise<ChatFolder> {
    const response = await apiClient.post("/social/chat-folders/", data);
    return response.data;
  },

  async update(id: number, data: UpdateFolderData): Promise<ChatFolder> {
    const response = await apiClient.patch(`/social/chat-folders/${id}/`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/social/chat-folders/${id}/`);
  },

  async reorder(folderIds: number[]): Promise<void> {
    try {
      await apiClient.patch("/social/chat-folders/reorder/", {
        folder_ids: folderIds,
      });
    } catch (error) {
      console.error("Error reordering folders:", error);
    }
  },

  async getPreview(id: number): Promise<FolderPreview> {
    if (id === -4) {
      try {
        const allChats = await readGroupChats();

        const discussionChats = allChats.filter(
          (chat: GroupChat) => chat.anime_id || chat.anime_title,
        );

        return {
          folder_id: id,
          chat_count: discussionChats.length,
          unread_count: discussionChats.reduce(
            (sum: number, d: GroupChat) => sum + (d.unread_count || 0),
            0,
          ),
          chats: discussionChats.map((d: GroupChat) => {
            const animePoster = d.anime_poster;
            const hasAnimePoster =
              animePoster &&
              typeof animePoster === "string" &&
              animePoster.trim() !== "";

            return {
              id: d.id,
              type: "group" as const,
              name: d.anime_title || d.name,
              description: d.description,
              avatar_url: hasAnimePoster
                ? getMediaUrl(animePoster)
                : d.avatar_url,

              anime_id: d.anime_id,
              anime_title: d.anime_title,
              anime_poster: hasAnimePoster ? getMediaUrl(animePoster) : null,
              members_count: d.members_count,
              unread_count: d.unread_count || 0,
              created_at: d.created_at,
              updated_at: d.updated_at || d.created_at,
              is_pinned: d.user_member_settings?.is_pinned || false,
              is_archived: d.user_member_settings?.is_archived || false,
              is_muted: d.user_member_settings?.is_muted || false,
              members: d.members || [],
              owner: d.owner || { id: 0, username: "" },
              is_public: d.is_public,
            } as Chat;
          }),
        };
      } catch (error) {
        if (!isRequestCancelled(error)) console.error("Error loading discussions:", error);
        return {
          folder_id: id,
          chat_count: 0,
          unread_count: 0,
          chats: [],
        };
      }
    }

    const response = await apiClient.get(`/social/chat-folders/${id}/preview/`);
    return response.data;
  },

  async getFolderChats(id: number): Promise<Chat[]> {
    if (id === -4) {
      try {
        const allChats = await readGroupChats();

        const discussionChats = allChats.filter(
          (chat: GroupChat) => chat.anime_id || chat.anime_title,
        );

        return discussionChats.map((d: GroupChat) => {
          const animePoster = d.anime_poster;
          const hasAnimePoster =
            animePoster &&
            typeof animePoster === "string" &&
            animePoster.trim() !== "";

          return {
            id: d.id,
            type: "group" as const,
            name: d.anime_title || d.name,
            description: d.description,
            avatar_url: hasAnimePoster
              ? getMediaUrl(animePoster)
              : d.avatar_url,

            anime_id: d.anime_id,
            anime_title: d.anime_title,
            anime_poster: hasAnimePoster ? getMediaUrl(animePoster) : null,
            members_count: d.members_count,
            unread_count: d.unread_count || 0,
            created_at: d.created_at,
            updated_at: d.updated_at || d.created_at,
            is_pinned: d.user_member_settings?.is_pinned || false,
            is_archived: d.user_member_settings?.is_archived || false,
            is_muted: d.user_member_settings?.is_muted || false,
            members: d.members || [],
            owner: d.owner || { id: 0, username: "" },
            is_public: d.is_public,
          } as Chat;
        });
      } catch (error) {
        console.error("Error loading folder chats:", error);
        return [];
      }
    }

    const response = await apiClient.get(`/social/chat-folders/${id}/chats/`);
    return response.data.results || response.data;
  },
};
