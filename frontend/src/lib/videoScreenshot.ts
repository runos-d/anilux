export interface CapturedVideoFrame {
  blob: Blob;
  timestamp: number;
  width: number;
  height: number;
}

export type ScreenshotDelivery = "copied" | "shared" | "downloaded" | "cancelled";

const MAX_CAPTURE_WIDTH = 1920;

const isAbortError = (error: unknown) =>
  error instanceof DOMException && error.name === "AbortError";

const isIos = () => {
  if (typeof navigator === "undefined") return false;
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
};

const canShareFile = (file: File) => {
  try {
    return typeof navigator.share === "function"
      && typeof navigator.canShare === "function"
      && navigator.canShare({ files: [file] });
  } catch {
    return false;
  }
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
};

export function dataUrlToBlob(dataUrl: string): Blob {
  const commaIndex = dataUrl.indexOf(",");
  if (commaIndex < 0) throw new Error("Некорректные данные изображения.");
  const header = dataUrl.slice(0, commaIndex);
  const base64 = dataUrl.slice(commaIndex + 1);
  const mime = /^data:([^;,]+)/.exec(header)?.[1] || "image/png";
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: mime });
}

export function captureVideoFrame(
  video: HTMLVideoElement,
  maxWidth = MAX_CAPTURE_WIDTH,
): CapturedVideoFrame {
  if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) {
    throw new Error("Кадр ещё не готов.");
  }

  const scale = Math.min(1, maxWidth / video.videoWidth);
  const width = Math.max(1, Math.round(video.videoWidth * scale));
  const height = Math.max(1, Math.round(video.videoHeight * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d", { alpha: false });
  if (!context) throw new Error("Браузер не поддерживает сохранение кадра.");

  const timestamp = video.currentTime;
  try {
    context.drawImage(video, 0, 0, width, height);
    return {
      blob: dataUrlToBlob(canvas.toDataURL("image/png")),
      timestamp,
      width,
      height,
    };
  } catch {
    throw new Error("Браузер не разрешает сохранить кадр. Попробуйте другой браузер.");
  }
}

export async function deliverScreenshot(blob: Blob, filename: string): Promise<ScreenshotDelivery> {
  const type = blob.type || "image/png";
  const file = new File([blob], filename, { type });

  if (isIos() && canShareFile(file)) {
    try {
      await navigator.share({ files: [file], title: filename });
      return "shared";
    } catch (error) {
      if (isAbortError(error)) return "cancelled";
    }
  }

  if (typeof ClipboardItem !== "undefined" && navigator.clipboard?.write) {
    try {
      await navigator.clipboard.write([new ClipboardItem({ [type]: blob })]);
      return "copied";
    } catch {}
  }

  if (!isIos() && canShareFile(file)) {
    try {
      await navigator.share({ files: [file], title: filename });
      return "shared";
    } catch (error) {
      if (isAbortError(error)) return "cancelled";
    }
  }

  downloadBlob(blob, filename);
  return "downloaded";
}
