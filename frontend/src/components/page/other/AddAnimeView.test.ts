import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
const fixture=vi.hoisted(()=>({get:vi.fn()}));
const router=vi.hoisted(()=>({push:vi.fn()}));
vi.mock('@/api/client',()=>({default:{get:fixture.get}}));
vi.mock('@/stores/auth',()=>({useAuthStore:()=>({isAuthenticated:true})}));
vi.mock('vue-router',()=>({useRouter:()=>router}));
import AddAnimeView from './AddAnimeView.vue';

describe('catalog addition search states',()=>{
  it('shows the empty message only for an empty successful search',async()=>{
    fixture.get.mockImplementation((url:string)=>Promise.resolve({data:url.includes('search-candidates')?{groups:[{name:'Результат',items:[{shikimori_id:1,title_ru:'Тайтл',title_en:'Title',kind:'tv',status:'ongoing',poster_url:'',exists_in_db:false}]}]}:{results:[]}}));
    const wrapper=mount(AddAnimeView,{global:{stubs:{RouterLink:true}}});
    await wrapper.get('.search-input').setValue('Поиск');await wrapper.get('.search-row button').trigger('click');await flushPromises();
    expect(wrapper.find('.result-card').exists()).toBe(true);expect(wrapper.find('.no-results').exists()).toBe(false);
    fixture.get.mockResolvedValue({data:{groups:[]}});await wrapper.get('.search-row button').trigger('click');await flushPromises();
    expect(wrapper.find('.result-card').exists()).toBe(false);expect(wrapper.find('.no-results').exists()).toBe(true);
    fixture.get.mockRejectedValue(new Error('Unavailable'));await wrapper.get('.search-row button').trigger('click');await flushPromises();
    expect(wrapper.find('.error-text').exists()).toBe(true);expect(wrapper.find('.no-results').exists()).toBe(false);
    wrapper.unmount();
  });

  it('opens the detail page when an existing anime card is clicked',async()=>{
    fixture.get.mockImplementation((url:string)=>Promise.resolve({data:url.includes('search-candidates')?{groups:[{name:'Результат',items:[{shikimori_id:1,title_ru:'Тайтл',title_en:'Title',kind:'tv',status:'ongoing',poster_url:'',exists_in_db:true,anime_slug:'title-slug'}]}]}:{results:[]}}));
    const wrapper=mount(AddAnimeView,{global:{stubs:{RouterLink:true}}});
    await wrapper.get('.search-input').setValue('Поиск');await wrapper.get('.search-row button').trigger('click');await flushPromises();
    await wrapper.get('.result-card').trigger('click');
    expect(router.push).toHaveBeenCalledWith('/anime/title-slug');
    wrapper.unmount();
  });
});
