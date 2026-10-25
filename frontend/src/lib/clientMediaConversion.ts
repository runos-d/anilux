export type PreparedMediaKind = "image" | "video" | "file";

export interface PreparedMediaFile {
  file: File;
  kind: PreparedMediaKind;
  converted: boolean;
}

const IMAGE_MAX_SIDE = 2560;
const IMAGE_QUALITY = 0.9;
const IMAGE_EXTENSIONS = /\.(?:jpe?g|png|gif|webp)$/i;
const VIDEO_EXTENSIONS = /\.(?:mp4|webm|mov|mkv|avi|m4v)$/i;

const replaceExtension = (name: string, extension: string) => {
  const stem = name.replace(/\.[^.]+$/, "") || "media";
  return `${stem}.${extension}`;
};

const canvasBlob = (canvas: HTMLCanvasElement, type: string, quality: number) =>
  new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Не удалось преобразовать изображение"))),
      type,
      quality,
    );
  });

async function imageToWebp(file: File): Promise<File> {
  if (file.type === "image/webp" || file.type === "image/gif") return file;

  const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  try {
    const scale = Math.min(1, IMAGE_MAX_SIDE / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext("2d", { alpha: true });
    if (!context) throw new Error("Не удалось подготовить изображение");
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await canvasBlob(canvas, "image/webp", IMAGE_QUALITY);
    return new File([blob], replaceExtension(file.name, "webp"), {
      type: "image/webp",
      lastModified: file.lastModified,
    });
  } finally {
    bitmap.close();
  }
}

/** Converts user-selected chat/post media before upload. Unknown files are untouched. */
export async function prepareMediaFile(file: File): Promise<PreparedMediaFile> {
  const isImage = file.type.startsWith("image/") || IMAGE_EXTENSIONS.test(file.name);
  const isVideo = file.type.startsWith("video/") || VIDEO_EXTENSIONS.test(file.name);
  if (isImage) {
    try {
      const prepared = await imageToWebp(file);
      return { file: prepared, kind: "image", converted: prepared !== file };
    } catch {
      return { file, kind: "image", converted: false };
    }
  }
  if (isVideo) {
    return { file, kind: "video", converted: false };
  }
  return { file, kind: "file", converted: false };
}

export async function prepareMediaFiles(files: File[]): Promise<PreparedMediaFile[]> {
  return Promise.all(files.map(prepareMediaFile));
}
