import { mount, flushPromises } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
const mocks=vi.hoisted(()=>({update:vi.fn(),put:vi.fn().mockResolvedValue(undefined),get:vi.fn().mockResolvedValue(undefined)}));
vi.mock('@/api/client',()=>({default:{}}));
vi.mock('@/stores/auth',()=>({useAuthStore:()=>({user:{id:1}})}));
vi.mock('@/stores/posts',()=>({usePostStore:()=>({upsert:(post:unknown)=>post})}));
vi.mock('@/lib/postAccount',()=>({postAccountGuard:()=>()=>{}}));
vi.mock('@/lib/postDrafts',()=>({postDraftGet:mocks.get,postDraftPut:mocks.put}));
vi.mock('@/lib/postPublication',()=>({updatePost:mocks.update}));
import EditPostModal from './EditPostModal.vue';
import type { FeedPost } from '@/api/feed';
describe('successful post edit',()=>{
  it('publishes the saved result and closes the form',async()=>{
    const post={id:2,text:'Before',version:1,attachments_data:[],media_files:[]} as unknown as FeedPost;
    const saved={...post,text:'After',version:2};mocks.update.mockResolvedValue(saved);
    const wrapper=mount(EditPostModal,{props:{post}});await flushPromises();
    await wrapper.find('textarea.text-input').setValue('After');await wrapper.find('.submit-btn').trigger('click');await flushPromises();
    expect(wrapper.emitted('updated')?.[0]).toEqual([saved]);expect(wrapper.emitted('close')).toHaveLength(1);
    wrapper.unmount();
  });
});
