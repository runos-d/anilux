import { describe, expect, it } from 'vitest';
import { validateMessageFiles, MAX_MESSAGE_FILE_BYTES } from './chatUploadLimits';
describe('message file size', () => {
  it('accepts a large video, multiple small files and exactly 250 MB in total', () => {
    expect(validateMessageFiles([{ size: 30 * 1024 * 1024 }])).toBeNull();
    expect(validateMessageFiles(Array.from({ length: 11 }, () => ({ size: 1 })))).toBeNull();
    expect(validateMessageFiles([{ size: MAX_MESSAGE_FILE_BYTES - 1 }, { size: 1 }])).toBeNull();
  });
  it('rejects an oversized message before sending it', () => {
    expect(validateMessageFiles([{ size: MAX_MESSAGE_FILE_BYTES }, { size: 1 }])).toContain('250 МБ');
  });
});
