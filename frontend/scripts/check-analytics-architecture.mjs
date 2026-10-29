import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../src/', import.meta.url));
const adapterSegment = join('analytics', 'adapters');
const violations = [];
const forbidden = [
  /\bwindow\s*\.\s*ym\b/,
  /\bwindow\s*\.\s*gtag\b/,
  /\bwindow\s*\.\s*dataLayer\b/,
  /mc\.yandex\.(?:ru|com)\/metrika/,
  /googletagmanager\.com\/gtag/,
];

function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) walk(path);
    else if (['.ts', '.vue', '.js'].includes(extname(entry.name))) {
      const local = relative(root, path);
      if (local.includes(adapterSegment) || /\.(?:test|spec)\.[cm]?[jt]s$/.test(local)) continue;
      const source = readFileSync(path, 'utf8');
      forbidden.forEach((pattern) => {
        if (pattern.test(source)) violations.push(`${local}: ${pattern}`);
      });
    }
  }
}

walk(root);
if (violations.length) {
  console.error(`Direct analytics provider usage is forbidden:\n${violations.join('\n')}`);
  process.exit(1);
}
