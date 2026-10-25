import { expect } from "@playwright/test";
import { argosScreenshot } from "@argos-ci/playwright";

export const themes = ["dark", "polnochnaya", "light"];
export const viewports = [
  { width: 390, height: 844 },
  { width: 1440, height: 1000 },
];

const screenshotCss = `
  *, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }
  [data-visual-test="volatile"] { visibility: hidden !important; }
`;

export async function waitForVisualReady(page) {
  await page.waitForFunction(() => document.documentElement.dataset.seoMode === "app", null, { timeout: 45_000 });
  await page.addStyleTag({ content: screenshotCss });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });
}

export async function assertStableSurface(page, label) {
  const measurements = await page.evaluate(() => ({
    width: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    text: document.body.innerText.trim().length,
  }));
  expect(measurements.text, `${label}: the page rendered no readable content`).toBeGreaterThan(0);
  expect(measurements.scrollWidth, `${label}: horizontal overflow`).toBeLessThanOrEqual(measurements.width + 2);
}

export async function captureSurface(page, name, { fullPage = true } = {}) {
  await argosScreenshot(page, name, {
    ariaSnapshot: true,
    argosCSS: screenshotCss,
    fullPage,
    threshold: 0,
    viewports,
  });
}

export async function addPaletteAudit(page, theme) {
  return page.evaluate((themeName) => {
    document.querySelector("[data-visual-palette-audit]")?.remove();
    document.querySelectorAll("[data-visual-color-outlier]").forEach((node) => {
      node.removeAttribute("data-visual-color-outlier");
      node.style.removeProperty("outline");
      node.style.removeProperty("outline-offset");
    });

    const probe = document.createElement("canvas").getContext("2d");
    const normalize = (value) => {
      if (!probe || !value || value === "transparent" || value === "none") return null;
      probe.fillStyle = "#000";
      probe.fillStyle = value;
      const normalized = probe.fillStyle;
      const match = normalized.match(/^#([0-9a-f]{6})$/i);
      if (!match) {
        const rgb = value.match(/rgba?\((\d+)[, ]+(\d+)[, ]+(\d+)(?:[, /]+([\d.]+))?\)/i);
        return rgb && Number(rgb[4] ?? 1) >= 0.12 ? [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])] : null;
      }
      return [0, 2, 4].map((offset) => Number.parseInt(match[1].slice(offset, offset + 2), 16));
    };
    const hsl = ([r, g, b]) => {
      r /= 255; g /= 255; b /= 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b), delta = max - min;
      let hue = 0;
      if (delta) hue = max === r ? ((g - b) / delta) % 6 : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
      hue = (hue * 60 + 360) % 360;
      const lightness = (max + min) / 2;
      const saturation = delta ? delta / (1 - Math.abs(2 * lightness - 1)) : 0;
      return { hue, saturation, lightness };
    };
    const root = getComputedStyle(document.documentElement);
    const accentRgb = normalize(root.getPropertyValue("--accent")) || [170, 110, 220];
    const accentHue = hsl(accentRgb).hue;
    const distance = (left, right) => Math.min(Math.abs(left - right), 360 - Math.abs(left - right));
    const counts = new Map();
    const outliers = [];
    const visible = [...document.body.querySelectorAll("*")].filter((element) => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return rect.width > 1 && rect.height > 1 && style.visibility !== "hidden" && style.display !== "none";
    });
    for (const element of visible) {
      const style = getComputedStyle(element);
      const colors = [style.color, style.backgroundColor, style.borderTopColor, style.fill, style.stroke];
      let foreign = false;
      for (const raw of colors) {
        const rgb = normalize(raw);
        if (!rgb) continue;
        const key = `rgb(${rgb.join(", ")})`;
        counts.set(key, (counts.get(key) || 0) + 1);
        const color = hsl(rgb);
        if (color.saturation >= 0.38 && color.lightness >= 0.18 && color.lightness <= 0.85 && distance(color.hue, accentHue) > 48) foreign = true;
      }
      if (foreign && outliers.length < 120) {
        element.setAttribute("data-visual-color-outlier", "true");
        element.style.setProperty("outline", "2px dashed #ffd84d", "important");
        element.style.setProperty("outline-offset", "-2px", "important");
        outliers.push(element);
      }
    }
    const palette = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
    const panel = document.createElement("aside");
    panel.setAttribute("data-visual-palette-audit", "true");
    Object.assign(panel.style, {
      position: "fixed", right: "12px", bottom: "12px", zIndex: "2147483647", width: "300px",
      padding: "14px", borderRadius: "12px", border: "1px solid rgba(255,255,255,.24)",
      background: "rgba(8,6,15,.96)", color: "#fff", font: "12px/1.45 system-ui,sans-serif",
      boxShadow: "0 18px 50px rgba(0,0,0,.5)",
    });
    panel.innerHTML = `<strong style="display:block;font-size:14px;margin-bottom:4px">Color audit · ${themeName}</strong><span style="color:#cfc7dc">Жёлтая рамка = насыщенный цвет вне оттенка темы. Решение об исключении принимается вручную.</span><div style="margin-top:9px">Кандидатов: <b>${outliers.length}</b></div><div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:9px">${palette.map(([color, count]) => `<span title="${color}: ${count}" style="width:20px;height:20px;border-radius:5px;background:${color};border:1px solid #ffffff55"></span>`).join("")}</div>`;
    document.body.append(panel);
    return { outliers: outliers.length, palette: palette.map(([color, count]) => ({ color, count })) };
  }, theme);
}

export async function capturePaletteAudit(page, name, theme) {
  const report = await addPaletteAudit(page, theme);
  await argosScreenshot(page, `${name}--palette-audit`, {
    argosCSS: screenshotCss,
    fullPage: true,
    threshold: 0,
  });
  return report;
}
