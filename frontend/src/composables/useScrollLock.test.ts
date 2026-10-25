import { describe, it, expect, afterEach } from 'vitest';
import { effectScope, ref } from 'vue';
import { useScrollLock } from './useScrollLock';

const scopes: ReturnType<typeof effectScope>[] = [];
afterEach(() => { scopes.splice(0).forEach(scope => scope.stop()); document.body.style.overflow = ''; });
describe('overlay scroll locks', () => {
  it('locks an initially open overlay and restores the previous style', () => {
    document.body.style.overflow = 'clip';
    const open = ref(true), scope = effectScope(); scopes.push(scope);
    scope.run(() => useScrollLock(open));
    expect(document.body.style.overflow).toBe('hidden');
    open.value = false;
    expect(document.body.style.overflow).toBe('clip');
  });
  it('closing or unmounting another overlay cannot unlock an open dialog', () => {
    const outer = ref(true), inner = ref(true), closed = ref(false);
    const a = effectScope(), b = effectScope(), c = effectScope(); scopes.push(a,b,c);
    a.run(() => useScrollLock(outer)); b.run(() => useScrollLock(inner)); c.run(() => useScrollLock(closed));
    c.stop(); outer.value = false;
    expect(document.body.style.overflow).toBe('hidden');
    b.stop(); expect(document.body.style.overflow).toBe('');
  });
});
