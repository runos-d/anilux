import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@vue/compiler-sfc';

const root = fileURLToPath(new URL('../src', import.meta.url));
const inventory = new Map();
const detached = new Set(['NewsView.vue','PeopleDetailView.vue','AnnouncementDetailView.vue','AnnouncementsView.vue','MyPlaylistsView.vue','PublicPlaylistsView.vue','KodikImport.vue','ModerationView.vue','CreateGroupView.vue','GroupsView.vue']);
['UserFeed.vue','UserSocialNetworks.vue','ProfileAbout.vue','OwnProfileView.vue','GlobalChatStyleModal.vue'].forEach(name => detached.add(name));
['ReportModal.vue','PostDetailModal.vue','RepostModal.vue','ForwardMessageModal.vue','DeleteAccountSettings.vue','AddCustomDubModal.vue','MuteChatModal.vue'].forEach(name => detached.add(name));
['CommentsModal.vue','Avatar.vue'].forEach(name => detached.add(name));
const clean = source => source.replace(/<!--[\s\S]*?-->/g, '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
const walk = file => {
  if (inventory.has(file) || !fs.existsSync(file) || detached.has(path.basename(file))) return;
  const source = fs.readFileSync(file, 'utf8');
  const { descriptor } = parse(source);
  const template = clean(descriptor.template?.content || '').replace(/<CursorEffects[^>]*\/\>/g, '');
  const script = clean((descriptor.script?.content || '') + '\n' + (descriptor.scriptSetup?.content || ''));
  inventory.set(file, { template, script, children: [] });
  for (const match of script.matchAll(/import\s+(\w+)\s+from\s+["']([^"']+\.vue)["']/g)) {
    if (!new RegExp(`<${match[1]}[\\s/>]`).test(template)) continue;
    const child = match[2].startsWith('@/') ? path.join(root, match[2].slice(2)) : path.resolve(path.dirname(file), match[2]);
    inventory.get(file).children.push(path.relative(root, child).replaceAll('\\', '/'));
    walk(child);
  }
  for (const match of script.matchAll(/import\s*\{([^}]+)\}\s*from\s*["']([^"']+)["']/g)) {
    const folder = match[2].startsWith('@/') ? path.join(root, match[2].slice(2)) : path.resolve(path.dirname(file), match[2]);
    const barrel = path.join(folder, 'index.ts');
    if (!fs.existsSync(barrel)) continue;
    const exports = fs.readFileSync(barrel, 'utf8');
    for (const name of match[1].split(',').map(value => value.trim())) {
      if (!new RegExp(`<${name}[\\s/>]`).test(template)) continue;
      const target = exports.match(new RegExp(`export\\s*\\{\\s*default\\s+as\\s+${name}\\s*\\}\\s*from\\s*["']([^"']+\\.vue)["']`));
      if (!target) continue;
      const child = path.resolve(folder, target[1]);
      inventory.get(file).children.push(path.relative(root, child).replaceAll('\\', '/'));
      walk(child);
    }
  }
  for (const match of script.matchAll(/import\(["']([^"']+\.vue)["']\)/g)) {
    const child = match[1].startsWith('@/') ? path.join(root, match[1].slice(2)) : path.resolve(path.dirname(file), match[1]);
    walk(child);
  }
};
walk(path.join(root, 'App.vue'));
const routes = clean(fs.readFileSync(path.join(root, 'router/index.ts'), 'utf8'));
for (const match of routes.matchAll(/["'](@\/components\/[^"']+\.vue)["']/g)) {
  walk(path.join(root, match[1].slice(2)));
}
const result = [...inventory].map(([file, data]) => ({ file: path.relative(root, file).replaceAll('\\', '/'), children: data.children,
  symbols: (data.template + '\n' + data.script).split('\n').map((line, i) => ({ line: i + 1, text: line.trim() }))
    .filter(row => /[\p{Extended_Pictographic}★☆×✕✖✓✔→←▸▾▴◀▶⚙❍⋯›‹↻]/u.test(row.text)) }));
fs.writeFileSync(path.resolve(root, '../../backend/data/local_release/ui-review/inventory.json'), JSON.stringify(result, null, 2));
console.log(result.length + ' candidate components; actual availability must be confirmed by navigation and conditions');
for (const item of result.filter(row => row.symbols.length)) console.log(item.file + '\n' + item.symbols.map(row => row.text).join('\n'));
