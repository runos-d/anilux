const enabled = (value: unknown): boolean =>
  typeof value === 'string' && ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase())

export const features = Object.freeze({
  dubs: enabled(import.meta.env.VITE_FEATURE_DUBS_ENABLED),
  reactor: enabled(import.meta.env.VITE_FEATURE_REACTOR_ENABLED),
  twoFactor: enabled(import.meta.env.VITE_FEATURE_TWO_FACTOR_ENABLED),
  studioReactions: enabled(import.meta.env.VITE_FEATURE_STUDIO_REACTIONS_ENABLED),
  studioSync: enabled(import.meta.env.VITE_FEATURE_STUDIO_SYNC_ENABLED),
})
