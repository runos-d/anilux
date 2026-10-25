import type { Anime4KShaderConstructor } from "anime4k.js";

export interface Anime4KVideoUpscaler {
  attachVideo(video: HTMLVideoElement, canvas: HTMLCanvasElement): void;
  start(): void;
  stop(): void;
  detachVideo(): void;
}

interface Anime4KVideoUpscalerConstructor {
  new (profile: Anime4KShaderConstructor[], fps?: number): Anime4KVideoUpscaler;
  isSupported(): boolean;
}

/** Load only the three shaders used by SIMPLE_M_2X instead of the full preset catalog. */
export const loadAnime4K = async () => {
  const [video, clamp, restore, upscale] = await Promise.all([
    import("anime4k.js/internal/video"),
    import("anime4k.js/internal/clamp-highlights"),
    import("anime4k.js/internal/restore-cnn-m"),
    import("anime4k.js/internal/upscale-cnn-m"),
  ]);

  return {
    VideoUpscaler: video.default as Anime4KVideoUpscalerConstructor,
    ANIME4KJS_SIMPLE_M_2X: [
      clamp.default,
      restore.default,
      upscale.default,
    ] as Anime4KShaderConstructor[],
  };
};
