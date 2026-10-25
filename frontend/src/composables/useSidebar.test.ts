import { nextTick } from 'vue';
import { beforeEach, expect, it, vi } from 'vitest';

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
});

it('applies rapid reversals immediately and persists the latest state', async () => {
  const sidebar = (await import('./useSidebar')).useSidebar();
  sidebar.toggleSidebar();
  expect(sidebar.isCollapsed.value).toBe(true);
  sidebar.toggleSidebar();
  expect(sidebar.isCollapsed.value).toBe(false);
  sidebar.toggleSidebar();
  await nextTick();
  expect(localStorage.getItem('sidebarCollapsed')).toBe('true');
  sidebar.expandSidebar();
  await nextTick();
  expect(localStorage.getItem('sidebarCollapsed')).toBe('false');
});

it('restores the saved desktop state independently of the mobile menu', async () => {
  localStorage.setItem('sidebarCollapsed', 'true');
  const sidebar = (await import('./useSidebar')).useSidebar();
  expect(sidebar.isCollapsed.value).toBe(true);
  sidebar.toggleMobileMenu();
  expect(sidebar.isMobileMenuOpen.value).toBe(true);
  sidebar.expandSidebar();
  expect(sidebar.isMobileMenuOpen.value).toBe(true);
  sidebar.closeMobileMenu();
  expect(sidebar.isMobileMenuOpen.value).toBe(false);
});
