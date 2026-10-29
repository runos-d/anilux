import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { RouterLink, createMemoryHistory, createRouter } from 'vue-router';
import SeoNavigation from './SeoNavigation.vue';
import navigation from '@/site-navigation.json';

describe('global footer', () => {
  it('renders the same links without an SEO request, including on errors and private routes', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [
      { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
    ] });
    await router.push('/');
    const wrapper = mount(SeoNavigation, { global: { plugins: [router] } });
    const expected = navigation.groups.flatMap(group => group.links.map(link => link.path));
    for (const path of ['/', '/profile', '/terms', '/missing']) {
      await router.push(path);
      expect(wrapper.find('footer').exists()).toBe(true);
      expect(wrapper.findAllComponents(RouterLink).map(link => link.props('to'))).toEqual(expected);
    }
    expect(wrapper.find('a[href^="mailto:"]').attributes('href')).toBe('mailto:' + navigation.email);
    expect(wrapper.text()).toContain('Для правообладателей');
    expect(wrapper.findAllComponents(RouterLink).filter(link => ['/contacts', '/license'].includes(String(link.props('to')))).map(link => link.text())).toEqual([
      'Помощь',
      'Связаться с администрацией',
      'Права на материалы',
    ]);
    expect(wrapper.find('.logo-icon svg').exists()).toBe(true);
    expect(wrapper.find('a[href^="/post/"]').exists()).toBe(false);
    wrapper.unmount();
  });
});
