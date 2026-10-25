const notificationPrefix = /^(?:👤\s+(?=Новый пользователь:)|🚨\s+(?=Новая жалоба:)|⚠️?\s+(?=Новая жалоба от ))/u;
const postPrefix = /^(?:🎉|🎯|👥|🏆|🥇|🥈|🥉|🏅|⭐)\s+(?=Новый уровень!|Победа в конкурсе!|Участие в конкурсе|Новая группа|Новый конкурс!|Достижение получено!|Важная отметка!)/u;

export function notificationTitle(title: string | null | undefined, type?: string): string {
  const text = title || '';
  return type === 'system' || type === 'warning' ? text.replace(notificationPrefix, '') : text;
}

export function postTitle(title: string | null | undefined, postType?: string): string {
  const text = title || '';
  return postType === 'system' ? text.replace(postPrefix, '') : text;
}
