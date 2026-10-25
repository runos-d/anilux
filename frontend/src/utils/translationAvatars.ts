const AVATAR_BASE = '/media/translation-logos/'

const EXT_MAP: Record<string, string> = {
  'AnimeLib': 'png',
  'AniMedia': 'png',
  'AnimeVost': 'png',
  'AnimeZaVoskresenye': 'png',
  'AniStar': 'png',
  'AniDUB': 'png',
  'MiraiDub': 'png',
  'SoundTeam': 'png',
  'AnimeReactor': 'png',
  'Azazel': 'png',
  'JAS': 'png',
  'KANSAI': 'png',
  'OSLIK': 'png',
  'RedRussian': 'png',
  'SilverRain': 'png',
  'Subtituls': 'png',
  'Tori': 'png',
  'VoicePlay': 'png',
  'AniWave': 'png',
  'Субтитры': 'png',
  'Оригинал': 'png',
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9а-яё_-]+/gi, ' ')
    .trim()
    .replace(/\s+/g, '-')
}

export function getTranslationAvatarUrl(name: string | undefined | null): string | undefined {
  if (!name) return undefined
  const ext = EXT_MAP[name]
  if (!ext) return undefined
  return `${AVATAR_BASE}${slugify(name)}.${ext}`
}
