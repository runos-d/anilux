import { useRouter } from "vue-router";
import {
  animeDiscussionsApi,
  type AnimeDiscussionGroup,
} from "@/api/animeDiscussions";

interface ApiError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
      error?: string;
    };
  };
}

const isNotFound = (err: unknown): boolean =>
  (err as ApiError)?.response?.status === 404;

export function useAnimeDiscussionNavigation() {
  const router = useRouter();

  const openDiscussionChat = async (
    group: AnimeDiscussionGroup,
  ): Promise<void> => {
    const chatId = group.chat_id || group.id;
    if (!chatId) {
      throw new Error("Не удалось получить ID чата");
    }
    await router.push(`/chats/${chatId}`);
  };

  const navigateToAnimeDiscussion = async (
    animeId: number,
  ): Promise<void> => {
    let group: AnimeDiscussionGroup;
    try {
      group = await animeDiscussionsApi.getDiscussionGroup(animeId);
    } catch (err) {
      if (isNotFound(err)) {
        group = await animeDiscussionsApi.createDiscussionGroup(animeId);
      } else {
        throw err;
      }
    }
    if (!group.user_joined) {
      group = await animeDiscussionsApi.joinDiscussionGroup(animeId);
    }
    await openDiscussionChat(group);
  };

  const navigateToFranchiseDiscussion = async (
    franchiseId: number,
  ): Promise<void> => {
    let group: AnimeDiscussionGroup;
    try {
      group = await animeDiscussionsApi.getFranchiseDiscussion(franchiseId);
    } catch (err) {
      if (isNotFound(err)) {
        group = await animeDiscussionsApi.joinFranchiseDiscussion(franchiseId);
      } else {
        throw err;
      }
    }
    await openDiscussionChat(group);
  };

  return { navigateToAnimeDiscussion, navigateToFranchiseDiscussion };
}
