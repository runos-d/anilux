export interface FranchiseCarouselEntry {
  id: number;
  slug?: string | null;
  anime_slug?: string | null;
  title_ru?: string | null;
  title_en?: string | null;
  kind?: string | null;
  year?: number | null;
  score?: number | null;
  status?: string | null;
  episodes?: number | null;
  poster?: string | null;
  poster_url?: string | null;
  poster_image_url?: string | null;
  genres?: Array<string | { id?: number; name?: string; slug?: string }> | null;
}
