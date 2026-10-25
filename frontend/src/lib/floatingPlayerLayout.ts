export function floatingPlayerLayout(viewport: { width: number; height: number; offsetLeft?: number; offsetTop?: number },
  size: { width: number; height: number }, position: { x: number; y: number },
  minimized: boolean, aspectRatio: number) {
  const availableWidth = Math.max(1, viewport.width - 20);
  const width = Math.min(minimized ? 280 : size.width, availableWidth);
  const scaledHeight = width < size.width ? width / Math.max(.1, aspectRatio) + 42 : size.height;
  const height = Math.min(minimized ? 42 : scaledHeight, Math.max(42, viewport.height - 20));
  const left = viewport.offsetLeft || 0, top = viewport.offsetTop || 0;
  return { width, height,
    x: Math.max(left, Math.min(position.x, left + viewport.width - width)),
    y: Math.max(top, Math.min(position.y, top + viewport.height - height)) };
}
