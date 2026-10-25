import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import LegalDocumentPage from './LegalDocumentPage.vue';

const sections = [
  { id: 'first', number: '01', title: 'Первый раздел' },
  { id: 'second', number: '02', title: 'Второй раздел' },
];

function mountDocument() {
  return mount(LegalDocumentPage, {
    props: {
      title: 'Документ',
      subtitle: 'Описание',
      updatedAt: '18.10.2026',
      sections,
    },
    slots: {
      intro: '<p>Введение</p>',
      first: '<p>Содержание первого раздела</p>',
      second: '<p>Содержание второго раздела</p>',
    },
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  });
}

describe('LegalDocumentPage', () => {
  it('renders a linked table of contents and opens the selected section', async () => {
    const wrapper = mountDocument();
    expect(wrapper.get('a[href="#first"]').text()).toContain('Первый раздел');
    expect(wrapper.get('a[href="#second"]').text()).toContain('Второй раздел');
    expect(wrapper.findAll('details').map(item => item.attributes('open'))).toEqual(['', undefined]);

    await wrapper.get('a[href="#second"]').trigger('click');
    expect(wrapper.findAll('details')[1]!.element.open).toBe(true);
  });

  it('expands and collapses every section', async () => {
    const wrapper = mountDocument();
    const button = wrapper.get('.legal-toc button');

    await button.trigger('click');
    expect(wrapper.findAll('details').every(item => item.element.open)).toBe(true);
    expect(button.text()).toBe('Свернуть все разделы');

    await button.trigger('click');
    expect(wrapper.findAll('details').every(item => !item.element.open)).toBe(true);
    expect(button.text()).toBe('Раскрыть все разделы');
  });
});
