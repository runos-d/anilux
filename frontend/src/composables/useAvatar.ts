import { getMediaUrl, getBackendOrigin } from "@/api/client";

const defaultAvatars = [
  "1.jpg", "2.jpg", "3.jpg", "4.jpg",
  "5.jpg", "6.jpg", "7.jpg", "8.jpg", 
  "9.jpg", "10.jpg", "11.jpg", "12.jpg",
  "13.jpg", "14.jpg", "15.jpg", "16.jpg",
  "17.jpg", "18.jpg", "19.jpg", "20.jpg",
];

const getCurrentFrontendOrigin = (): string => {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  return 'http://localhost:5173';
};

const normalizeAvatarUrl = (url: string): string => {
  try {
    const parsed = new URL(url);
    const frontendOrigin = getCurrentFrontendOrigin();

    if (parsed.origin === frontendOrigin) {
      return getBackendOrigin() + parsed.pathname + parsed.search + parsed.hash;
    }
  } catch {
  }

  return url;
};

export function useAvatar() {
  const getAvatarUrl = (
    avatarPath: string | null | undefined,
    userId?: number,
  ): string => {
    if (!avatarPath || avatarPath.trim() === "") {
      if (userId !== undefined) {
        const randomIndex = Math.abs(userId) % defaultAvatars.length;
        return getMediaUrl(`/data/media/def_avatars/${defaultAvatars[randomIndex]}`) || `/data/media/def_avatars/${defaultAvatars[randomIndex]}`;
      }
      const randomIndex = 0;
      return getMediaUrl(`/data/media/def_avatars/${defaultAvatars[randomIndex]}`) || `/data/media/def_avatars/${defaultAvatars[randomIndex]}`;
    }

    if (avatarPath.startsWith("http://") || avatarPath.startsWith("https://")) {
      const normalized = normalizeAvatarUrl(avatarPath);
      if (normalized !== avatarPath) {
        return getMediaUrl(normalized) || normalized;
      }
      return avatarPath;
    }

    const resolved = getMediaUrl(avatarPath);
    if (resolved) return resolved;

    return getMediaUrl(`/data/media/def_avatars/${defaultAvatars[0]}`) || `/data/media/def_avatars/${defaultAvatars[0]}`;
  };

  const getUserInitials = (user: {
    display_name?: string;
    username: string;
  }): string => {
    const name = user.display_name || user.username || "";
    return name.charAt(0).toUpperCase();
  };

  const getInitialsFromName = (name: string): string => {
    if (!name) return "?";
    return name.charAt(0).toUpperCase();
  };

  const getInitialsColor = (name: string): string => {
    if (!name || name.length === 0) return "#667eea";
    const colors = [
      "#667eea",
      "#764ba2",
      "#f093fb",
      "#f5576c",
      "#4facfe",
      "#00f2fe",
      "#43e97b",
      "#38f9d7",
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index]!;
  };

  return {
    getAvatarUrl,
    getUserInitials,
    getInitialsFromName,
    getInitialsColor,
  };
}
