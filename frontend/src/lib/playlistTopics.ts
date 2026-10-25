export const playlistTopics: Record<string, string> = {
  beginners: 'Для новичков', evening: 'На один вечер', friends: 'Для компании',
  cozy: 'Уютное и спокойное', adventure: 'Дух приключений', thoughtful: 'Есть о чём подумать',
};
export const playlistTopicGroups = [
  { id: 'occasion', name: 'Сценарий просмотра', description: 'Для кого или когда смотреть' },
  { id: 'mood', name: 'Настроение', description: 'Какое впечатление оставляет подборка' },
];
export const topicGroup = (slug: string) => ['beginners', 'evening', 'friends'].includes(slug) ? 'occasion' : 'mood';
export const playlistTopicName = (slug: string) => playlistTopics[slug] || slug;
