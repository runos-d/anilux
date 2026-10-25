import fs from 'node:fs';
import ts from 'typescript';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@vue/compiler-sfc';
const root=fileURLToPath(new URL('../src',import.meta.url));
const source = fs.readFileSync(path.join(root,'components/icons/SakuraIcon.vue'),'utf8');
const {descriptor}=parse(source);
const module={};
new Function('exports',ts.transpileModule(descriptor.script.content,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText)(module);
const names=new Set(module.ICON_NAMES);
const rows=JSON.parse(fs.readFileSync(path.resolve(root,'../../backend/data/local_release/ui-review/inventory.json'),'utf8'));
const missing=new Map();
for(const row of rows){
  const content=fs.readFileSync(path.join(root,row.file),'utf8').replace(/<!--[\s\S]*?-->|\/\*[\s\S]*?\*\/|^\s*\/\/.*$/gm,'');
  for(const match of content.matchAll(/(?:<SakuraIcon\b[^>]*?(?<!:)\bname="|\bicon:\s*["'])([a-z][a-z0-9-]*)["']/g)){
    if(!names.has(match[1])) missing.set(match[1],[...(missing.get(match[1])||[]),row.file]);
  }
}
for(const [name,files] of missing) console.log(name+': '+[...new Set(files)].join(', '));
