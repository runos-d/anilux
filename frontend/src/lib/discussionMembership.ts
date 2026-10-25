import apiClient from "@/api/client";

type Discussion = {
  id: number; type: string; is_public?: boolean; discussion_type?: string;
  anime_id?: number | null; franchise_id?: number | null; user_role?: unknown;
};

/** Browsing the list stays read-only; opening a public discussion joins it. */
export async function joinOpenedDiscussion<T extends Discussion>(detail: T, signal: AbortSignal): Promise<T> {
  if (detail.type !== "group" || !detail.is_public || detail.user_role) return detail;
  const path = detail.discussion_type === "anime" && detail.anime_id
    ? `/social/anime/${detail.anime_id}/discussion-group/join/`
    : detail.discussion_type === "franchise" && detail.franchise_id
      ? `/social/franchise/${detail.franchise_id}/discussion/join/` : null;
  if (!path) return detail;
  const { data } = await apiClient.post(path, {}, { signal });
  if (Number(data.id) !== detail.id) throw new Error("Обсуждение изменилось, откройте его заново");
  return { ...detail, ...data, type: "group" };
}
