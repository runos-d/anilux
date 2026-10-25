import { describe, expect, it } from 'vitest';
import { notificationTitle, postTitle } from './systemUiText';

describe('legacy decorative prefixes in application headings', () => {
  it.each([
    ['👤 Новый пользователь: @test', 'system', 'Новый пользователь: @test'],
    ['🚨 Новая жалоба: Пост', 'system', 'Новая жалоба: Пост'],
    ['⚠️ Новая жалоба от @test', 'warning', 'Новая жалоба от @test'],
  ])('renders %s without the system prefix', (title, type, expected) => expect(notificationTitle(title, type)).toBe(expected));
  it('preserves message/user content and unknown headings', () => {
    expect(notificationTitle('👤 Новый пользователь: поздравляю!', 'message')).toBe('👤 Новый пользователь: поздравляю!');
    expect(notificationTitle('🌸 Мой текст', 'system')).toBe('🌸 Мой текст');
    expect(notificationTitle('Новый пользователь: @🌸', 'system')).toBe('Новый пользователь: @🌸');
  });
  it('changes only an application-generated system post title', () => {
    expect(postTitle('🏆 Достижение получено!', 'system')).toBe('Достижение получено!');
    expect(postTitle('🏆 Достижение получено!', 'post')).toBe('🏆 Достижение получено!');
  });
});
