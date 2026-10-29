import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { defineComponent, nextTick, reactive, ref, h, KeepAlive } from 'vue';
import { mount, type VueWrapper } from '@vue/test-utils';

type CatalogRead = (...args: unknown[]) => Promise<{ results: never[]; count: number; total_pages: number }>;
interface TestRoute { path: string; query: Record<string, string> }
const catalogRead = vi.hoisted(() => vi.fn<CatalogRead>(async () => ({ results: [], count: 0, total_pages: 1 })));
const navigation=vi.hoisted(()=>({route:{path:'/anime',query:{section:'catalog'}} as TestRoute,replace:vi.fn()}));
vi.mock('vue-router',()=>({useRoute:()=>navigation.route,useRouter:()=>({replace:navigation.replace})}));
vi.mock('@/lib/initialContent',()=>({afterInitialContent:()=>{}}));
vi.mock('./useCachedReads',()=>({useCachedReads:()=>catalogRead}));
import { catalogFiltersFromQuery, useAnimeSections } from './useAnimeSections';
let wrapper:VueWrapper;
let sections:ReturnType<typeof useAnimeSections>;
beforeEach(()=>{
  localStorage.clear(); navigation.replace.mockReset();
  navigation.route=reactive({path:'/anime',query:{section:'catalog'}});
  wrapper=mount(defineComponent({setup(){sections=useAnimeSections();return()=>null;}}));
});
afterEach(()=>wrapper.unmount());

it('keeps the latest clicked section when earlier navigation resolves last',async()=>{
  let finishFirst:()=>void=()=>{},finishSecond:()=>void=()=>{};
  navigation.replace.mockImplementationOnce(()=>new Promise<void>(r=>{finishFirst=r;}))
    .mockImplementationOnce(()=>new Promise<void>(r=>{finishSecond=r;}));
  const first=sections.switchSection('ongoings');
  expect(sections.currentSection.value).toBe('ongoings');
  const second=sections.switchSection('calendar');
  expect(sections.currentSection.value).toBe('calendar');
  finishSecond();await second;finishFirst();await first;
  expect(sections.currentSection.value).toBe('calendar');
});

it('handles browser history without issuing another router replacement',async()=>{
  navigation.replace.mockClear();
  navigation.route.query.section='ongoings';await nextTick();
  expect(sections.currentSection.value).toBe('ongoings');
  expect(navigation.replace).not.toHaveBeenCalled();
});

it('activates currently watching when footer navigation changes only the query', async () => {
  navigation.replace.mockClear();
  navigation.route.query.section = 'currently_watching';
  await nextTick();
  expect(sections.currentSection.value).toBe('currently_watching');
  expect(navigation.replace).not.toHaveBeenCalled();
});

 it('preserves a local catalog search after opening a card and returning', async () => {
  wrapper.unmount();
  const visible = ref(true);
  const Child = defineComponent({ setup() { sections = useAnimeSections(); return () => null; } });
  wrapper = mount(defineComponent({ setup() { return () => h(KeepAlive, null, { default: () => visible.value ? h(Child) : h('div') }); } }));
  await nextTick();
  await sections.fetchCatalog(1, { search: 'тестовое' });
  visible.value = false;
  await nextTick();
  navigation.route.path = '/franchise/test';
  await nextTick();
  navigation.route.path = '/anime';
  visible.value = true;
  await nextTick();
  catalogRead.mockClear();
  await sections.fetchCatalog(1);
  expect(catalogRead.mock.calls.at(-1)?.[0]).toEqual(expect.arrayContaining([expect.objectContaining({ search: 'тестовое' })]));
});

it('reads catalog filters from the public URL and keeps them for pagination', async () => {
  wrapper.unmount();
  navigation.route=reactive({path:'/anime',query:{section:'catalog',genres:'Авангард',status:'finished,released'}});
  wrapper=mount(defineComponent({setup(){sections=useAnimeSections();return()=>null;}}));
  await nextTick();
  catalogRead.mockClear();
  await sections.fetchCatalog(2);
  expect(catalogRead.mock.calls.at(-1)?.[0]).toEqual(expect.arrayContaining([
    expect.objectContaining({page:2,genres:'Авангард',status:'finished,released'}),
  ]));
});

it('parses all supported collection query values', () => {
  expect(catalogFiltersFromQuery({genres:'Драма,Авангард',year_from:'2016',show_only_franchises:'true'})).toEqual({
    genres:['Драма','Авангард'],year_from:2016,show_only_franchises:true,
  });
});
