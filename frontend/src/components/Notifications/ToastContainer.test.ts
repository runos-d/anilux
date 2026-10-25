import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
const fixtures=vi.hoisted(()=>({onClick:vi.fn(),action:vi.fn(),remove:vi.fn()}));
vi.mock('@/composables/useToast',()=>({useToast:()=>({toasts:[{id:1,type:'info',message:'Подсказка',duration:60000,onClick:fixtures.onClick,action:{label:'Настроить прогресс',handler:fixtures.action}}],removeToast:fixtures.remove})}));
import ToastContainer from './ToastContainer.vue';

describe('toast actions',()=>{
  it('runs callbacks once and offers the action as a named button',async()=>{
    const wrapper=mount(ToastContainer,{attachTo:document.body});
    (document.querySelector('.toast') as HTMLElement).click();
    expect(fixtures.onClick).toHaveBeenCalledTimes(1);expect(fixtures.action).toHaveBeenCalledTimes(1);
    const button=document.querySelector('.toast-action') as HTMLButtonElement;
    expect(button.textContent).toBe('Настроить прогресс');button.click();
    expect(fixtures.action).toHaveBeenCalledTimes(2);expect(fixtures.onClick).toHaveBeenCalledTimes(1);
    expect(fixtures.remove).toHaveBeenCalledWith(1);wrapper.unmount();
  });
});
