import { mkdirSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const frontendDir = fileURLToPath(new URL('..', import.meta.url))
const viteEntry = fileURLToPath(new URL('../node_modules/vite/bin/vite.js', import.meta.url))
const env = { ...process.env }

if (process.platform === 'win32') {
  const buildTemp = fileURLToPath(new URL('../.build-tmp/', import.meta.url))
  mkdirSync(buildTemp, { recursive: true })
  env.TEMP = buildTemp
  env.TMP = buildTemp
}

const result = spawnSync(
  process.execPath,
  [viteEntry, 'build', ...process.argv.slice(2)],
  { cwd: frontendDir, env, stdio: 'inherit' },
)

if (result.error) throw result.error
process.exit(result.status ?? 1)
