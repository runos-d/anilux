/**
 * Эффекты прокрутки: карточки плавно появляются, когда доезжают до экрана.
 *
 * Работает только когда включено в настройках оформления. Скрываются лишь те
 * карточки, что на момент обнаружения находятся ниже видимой области: всё, что
 * уже на экране или в горизонтальной карусели, остаётся как есть.
 * Для сдвига используется свойство `translate`, поэтому hover-эффекты на
 * `transform` у самих карточек не конфликтуют.
 */

const CARD_SELECTOR = [
  ".anime-poster",
  ".poster-wrap",
  ".col-card",
  ".lib-card",
  ".playlist-card",
  ".post-card",
  ".user-card",
  ".rec-card-wrap",
  ".cwc-wrap",
  ".rwc-wrap",
].join(",");

const PRE_CLASS = "sr-pre";

let enabled = false;
let io: IntersectionObserver | null = null;
let mo: MutationObserver | null = null;
let scanScheduled = false;
const seen = new WeakSet<Element>();

const ANIM_CLASS = "sr-anim";

const reveal = (el: Element) => {
  el.classList.add(ANIM_CLASS);
  el.classList.remove(PRE_CLASS);
  io?.unobserve(el);
  window.setTimeout(() => {
    el.classList.remove(ANIM_CLASS);
    (el as HTMLElement).style.removeProperty("transition-delay");
  }, 1000);
};

const scan = () => {
  scanScheduled = false;
  if (!enabled || !io) return;

  let batchIndex = 0;
  document.querySelectorAll(CARD_SELECTOR).forEach((el) => {
    if (seen.has(el)) return;
    seen.add(el);

    const rect = el.getBoundingClientRect();
    const belowFold = rect.top >= window.innerHeight && rect.left < window.innerWidth;
    if (!belowFold) return;

    (el as HTMLElement).style.transitionDelay = `${Math.min(batchIndex, 6) * 45}ms`;
    batchIndex += 1;
    el.classList.add(PRE_CLASS);
    io!.observe(el);
  });
};

const scheduleScan = () => {
  if (scanScheduled) return;
  scanScheduled = true;
  window.requestAnimationFrame(scan);
};

const start = () => {
  if (io || typeof IntersectionObserver === "undefined") return;

  io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) reveal(entry.target);
      });
    },
    { threshold: 0.05, rootMargin: "0px 0px -4% 0px" },
  );

  mo = new MutationObserver(scheduleScan);
  mo.observe(document.body, { childList: true, subtree: true });
  scheduleScan();
};

const stop = () => {
  mo?.disconnect();
  io?.disconnect();
  mo = null;
  io = null;
  document.querySelectorAll(`.${PRE_CLASS}, .${ANIM_CLASS}`).forEach((el) => {
    el.classList.remove(PRE_CLASS, ANIM_CLASS);
    (el as HTMLElement).style.removeProperty("transition-delay");
  });
};

export const setScrollRevealEnabled = (value: boolean) => {
  if (typeof document === "undefined" || value === enabled) return;
  enabled = value;
  if (!value) {
    stop();
    return;
  }
  const begin = () => start();
  if (document.body) begin();
  else document.addEventListener("DOMContentLoaded", begin, { once: true });
};
