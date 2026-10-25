import { mount, flushPromises } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
vi.mock('vue-router',()=>({useRoute:()=>({params:{}})}));
vi.mock('@/api',()=>({default:{get:vi.fn().mockResolvedValue({data:[{id:1,is_unlocked:true,progress:10,progress_percentage:100,achievement:{id:1,name:'Достижение',description:'Описание',icon_svg:null,category:'basic',level:'bronze',condition_value:10}}]})}}));
import AchievementsView from './AchievementsView.vue';
import UserAchievements from '@/components/Profile/UserAchievements.vue';
const wrappers:ReturnType<typeof mount>[]=[];
afterEach(()=>wrappers.splice(0).forEach(wrapper=>wrapper.unmount()));
describe('achievement details in active places',()=>{
  it.each([AchievementsView,UserAchievements])('opens the dialog for a clicked card and uses an SVG fallback',async component=>{
    const wrapper=mount(component,{props:{userId:1},global:{stubs:{RouterLink:true}},attachTo:document.body});wrappers.push(wrapper);await flushPromises();
    await wrapper.find('.achievement-card').trigger('click');await flushPromises();
    const detail=document.querySelector('.achievement-detail');expect(detail).not.toBeNull();
    expect(detail?.querySelector('svg')).not.toBeNull();expect(detail?.querySelector('img')).toBeNull();
    (document.querySelector('.modal-close') as HTMLButtonElement).click();await flushPromises();
    expect(document.querySelector('.achievement-detail')).toBeNull();
  });
});
