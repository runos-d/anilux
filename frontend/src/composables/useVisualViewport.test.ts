import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useVisualViewport } from './useVisualViewport';
afterEach(() => vi.unstubAllGlobals());
describe('phone keyboard viewport', () => {
  it('updates fixed layout bounds when only the visual viewport shrinks, then cleans up', () => {
    const viewport=Object.assign(new EventTarget(),{height:844,offsetTop:0});
    vi.stubGlobal('visualViewport',viewport);
    const wrapper=mount(defineComponent({setup(){useVisualViewport();return()=>null;}}));
    expect(document.documentElement.style.getPropertyValue('--viewport-height')).toBe('844px');
    viewport.height=360; viewport.offsetTop=30; viewport.dispatchEvent(new Event('resize'));
    expect(document.documentElement.style.getPropertyValue('--viewport-height')).toBe('360px');
    expect(document.documentElement.style.getPropertyValue('--viewport-top')).toBe('30px');
    wrapper.unmount();
    expect(document.documentElement.style.getPropertyValue('--viewport-height')).toBe('');
    viewport.dispatchEvent(new Event('resize'));
    expect(document.documentElement.style.getPropertyValue('--viewport-height')).toBe('');
  });
});
