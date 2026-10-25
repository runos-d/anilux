declare module "anime4k.js/internal/video" {
  const VideoUpscaler: unknown;
  export default VideoUpscaler;
}

declare module "anime4k.js/internal/clamp-highlights" {
  import type { Anime4KShaderConstructor } from "anime4k.js";
  const shader: Anime4KShaderConstructor;
  export default shader;
}

declare module "anime4k.js/internal/restore-cnn-m" {
  import type { Anime4KShaderConstructor } from "anime4k.js";
  const shader: Anime4KShaderConstructor;
  export default shader;
}

declare module "anime4k.js/internal/upscale-cnn-m" {
  import type { Anime4KShaderConstructor } from "anime4k.js";
  const shader: Anime4KShaderConstructor;
  export default shader;
}
