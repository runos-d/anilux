import { mount, flushPromises } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({get:vi.fn()}));
vi.mock('@/api/client', () => ({default:mocks}));
import AchievementsManager from './AchievementsManager.vue';

afterEach(() => mocks.get.mockReset());
describe('admin achievement collection', () => {
  it('renders a paginated DRF response without treating null pagination links as rows', async () => {
    mocks.get.mockImplementation((url:string) => Promise.resolve({data:url.includes('condition_types') ? {posts:'Посты'} : {
      count:1,next:null,previous:null,results:[{id:1,name:'Проверка',description:'Описание',level:'bronze',category:'basic',condition_type:'posts',condition_value:1,is_active:true}],
    }}));
    const wrapper=mount(AchievementsManager);
    await flushPromises();
    expect(wrapper.findAll('.am-item')).toHaveLength(1);
    expect(wrapper.find('.am-item-name').text()).toBe('Проверка');
    await wrapper.find('.am-item').trigger('click');
    expect(wrapper.find('input').exists()).toBe(true);
    await wrapper.get('.am-create-btn').trigger('click');
    expect(wrapper.get('.am-editor h3').text()).toBe('Новое достижение');
    expect(wrapper.get('.am-form input[required]').element).toHaveProperty('value', '');
    expect(wrapper.find('.am-main-empty').exists()).toBe(false);
    wrapper.unmount();
  });
});
