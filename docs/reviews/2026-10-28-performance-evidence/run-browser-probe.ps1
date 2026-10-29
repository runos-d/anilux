param(
    [ValidateSet('all-routes', 'stress', 'details', 'watch', 'watch-race', 'navigation')]
    [string]$Probe = 'all-routes',
    [string]$Session = 'animecore-performance'
)
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$fixture = Get-Content (Join-Path $projectRoot 'frontend/tests/visual/fixtures.js') -Raw
$fixture = $fixture -replace '(?m)^export ', ''
$body = Get-Content (Join-Path $PSScriptRoot "browser-$Probe.js") -Raw
$networkGuard = @'
await page.context().route('**/*', route => {
  const url = new URL(route.request().url());
  return ['http:', 'https:'].includes(url.protocol) && !['127.0.0.1', 'localhost'].includes(url.hostname)
    ? route.fulfill({ status: 404, body: '' }) : route.fallback();
});
'@
$scriptPath = Join-Path ([IO.Path]::GetTempPath()) "animecore-performance-$Probe-replay.js"
Set-Content -LiteralPath $scriptPath -Value "async originalPage => { const context = await originalPage.context().browser().newContext({ serviceWorkers: 'block' }); const page = await context.newPage(); try {`n$fixture`n$networkGuard`n$body`n} finally { await context.close(); } }" -Encoding utf8
& playwright-cli "-s=$Session" run-code "--filename=$scriptPath"
