import { readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const assets = join(process.cwd(), 'dist', 'assets')
const files = readdirSync(assets)
const largest = (pattern) => files
  .filter((name) => pattern.test(name))
  .map((name) => ({ name, bytes: statSync(join(assets, name)).size }))
  .sort((a, b) => b.bytes - a.bytes)[0]

const budgets = [
  { label: 'entry JavaScript', file: largest(/^index-.*\.js$/), max: 350 * 1024 },
  { label: 'entry CSS', file: largest(/^index-.*\.css$/), max: 80 * 1024 },
]

let failed = false
for (const budget of budgets) {
  if (!budget.file) throw new Error(`Unable to find ${budget.label}`)
  const ok = budget.file.bytes <= budget.max
  console.log(`${ok ? 'PASS' : 'FAIL'} ${budget.label}: ${budget.file.name} ${budget.file.bytes}/${budget.max} bytes`)
  failed ||= !ok
}
if (failed) process.exit(1)
