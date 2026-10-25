export const KODIK_API_TOKEN = import.meta.env.VITE_KODIK_API_TOKEN;
export const KODIK_API_BASE = import.meta.env.VITE_KODIK_API_BASE;
export const KODIK_PLAYER_BASE = import.meta.env.VITE_KODIK_PLAYER_BASE;
export const KODIK_DB_BASE = import.meta.env.VITE_KODIK_DB_BASE;
export const KODIK_SCREENSHOTS_BASE = import.meta.env.VITE_KODIK_SCREENSHOTS_BASE;
export const KODIK_SOCIAL_BASE = import.meta.env.VITE_KODIK_SOCIAL_BASE;

const KODIK_OLD_PLAYER_DOMAINS = ["kodik.cc", "kodik.info", "kodik.biz", "kodikai.com"];

export function normalizeKodikPlayerLink(link: string): string {
  if (!link) return link;

  let url = link;
  if (url.startsWith("//")) {
    url = "https:" + url;
  } else if (!url.startsWith("http")) {
    url = "https://" + url;
  }

  for (const oldDomain of KODIK_OLD_PLAYER_DOMAINS) {
    if (url.includes(oldDomain)) {
      url = url.replace(oldDomain, "kodikplayer.com");
      break;
    }
  }

  return url;
}
