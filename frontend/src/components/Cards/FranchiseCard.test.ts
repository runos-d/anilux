import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks=vi.hoisted(()=>({get:vi.fn(),reminder:vi.fn(),addItem:vi.fn(),setFranchiseFavorite:vi.fn(),favoriteIds:new Set<number>(),error:vi.fn()}));
vi.mock('vue-router',()=>({useRouter:()=>({push:vi.fn()})}));
vi.mock('@/api/client',()=>({default:{get:mocks.get},getMediaUrl:(url:string)=>url}));
vi.mock('@/api/playlists',()=>({default:{getMyPlaylists:vi.fn().mockResolvedValue({data:[]}),addItemToPlaylist:mocks.addItem,setFranchiseFavorite:mocks.setFranchiseFavorite}}));
vi.mock('@/api/reminders',()=>({default:{createReminder:mocks.reminder}}));
vi.mock('@/composables/useToast',()=>({useToast:()=>({success:vi.fn(),error:mocks.error})}));
vi.mock('@/composables/useAnimeDiscussionNavigation',()=>({useAnimeDiscussionNavigation:()=>({navigateToFranchiseDiscussion:vi.fn()})}));
vi.mock('@/stores/favorites',()=>({useFavoritesStore:()=>({loaded:true,ensureLoaded:vi.fn().mockResolvedValue(undefined),isFavorite:(id:number)=>mocks.favoriteIds.has(id),commitIdsFavorite:async(ids:number[],value:boolean)=>ids.forEach(id=>value?mocks.favoriteIds.add(id):mocks.favoriteIds.delete(id))})}));
import FranchiseCard from './FranchiseCard.vue';

type TestFranchise={id:number;name:string;slug?:string;is_favorite?:boolean;entries?:Array<{id:number;title_ru:string}>};
const mountCard=(franchise:TestFranchise={id:16,name:'Франшиза',slug:'franchise'})=>mount(FranchiseCard,{props:{franchise},global:{stubs:{OptimizedImage:true,PlaylistSelectModal:{name:'PlaylistSelectModal',props:['show','anime'],template:'<div v-if="show" class="playlist-fixture"></div>'},ReminderModal:{name:'ReminderModal',props:['show','anime'],template:'<div v-if="show" class="reminder-fixture"></div>'}}}});
describe('franchise card actions',()=>{
  beforeEach(()=>{vi.clearAllMocks();mocks.favoriteIds.clear();});
  it('keeps favorite and playlist actions hidden',()=>{
    const wrapper=mountCard();
    expect(wrapper.find('.favorite-btn').exists()).toBe(false);
    expect(wrapper.find('.playlist-btn').exists()).toBe(false);
    wrapper.unmount();
  });
  it('resolves real parts before opening a reminder',async()=>{
    mocks.get.mockResolvedValue({data:{entries:[{id:202,title_ru:'Первая часть',status:'released'},{id:205,title_ru:'Продолжение',status:'ongoing'}]}});
    const wrapper=mountCard();
    await wrapper.get('.reminder-btn').trigger('click');await flushPromises();
    expect(mocks.get).toHaveBeenCalledWith('/anime/franchises/franchise/');
    expect(wrapper.findComponent({name:'ReminderModal'}).props('anime').id).toBe(205);
    wrapper.unmount();
  });
  it('leaves an unavailable action closed and reports an error',async()=>{
    mocks.get.mockRejectedValueOnce(new Error('Unavailable'));
    const wrapper=mountCard();await wrapper.get('.reminder-btn').trigger('click');await flushPromises();
    expect(wrapper.find('.reminder-fixture').exists()).toBe(false);expect(mocks.error).toHaveBeenCalled();wrapper.unmount();
  });
});
