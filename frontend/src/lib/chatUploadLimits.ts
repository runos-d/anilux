export const MAX_MESSAGE_FILE_BYTES = 250 * 1024 * 1024;

export function validateMessageFiles(files: Pick<File, 'size'>[]): string | null {
  return files.reduce((sum, file) => sum + file.size, 0) > MAX_MESSAGE_FILE_BYTES
    ? 'Общий размер файлов в сообщении не должен превышать 250 МБ' : null;
}
