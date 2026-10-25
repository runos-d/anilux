import { afterEach, describe, expect, it, vi } from 'vitest';
import { dataUrlToBlob, deliverScreenshot } from './videoScreenshot';

const originalClipboard = Object.getOwnPropertyDescriptor(navigator, 'clipboard');

afterEach(() => {
  vi.unstubAllGlobals();
  if (originalClipboard) {
    Object.defineProperty(navigator, 'clipboard', originalClipboard);
  } else {
    Reflect.deleteProperty(navigator, 'clipboard');
  }
});

describe('video screenshot', () => {
  it('converts a PNG data URL to a blob', () => {
    const blob = dataUrlToBlob('data:image/png;base64,AAAA');

    expect(blob.type).toBe('image/png');
    expect(blob.size).toBe(3);
  });

  it('copies the frame to the clipboard when image writing is supported', async () => {
    const write = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { write },
    });
    vi.stubGlobal('ClipboardItem', class {
      constructor(readonly items: Record<string, Blob>) {}
    });

    const result = await deliverScreenshot(
      new Blob(['png'], { type: 'image/png' }),
      'screenshot.png',
    );

    expect(result).toBe('copied');
    expect(write).toHaveBeenCalledOnce();
    expect(write).toHaveBeenCalledWith([expect.any(ClipboardItem)]);
  });
});
