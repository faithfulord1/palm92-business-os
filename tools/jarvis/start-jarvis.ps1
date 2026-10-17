$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath './dist/index.html')) { throw 'Extract the complete Jarvis package, including dist.' }
$candidates = @()
if ($env:PALM92_PYTHON) { $candidates += $env:PALM92_PYTHON }
$candidates += Join-Path $env:LOCALAPPDATA 'Programs/Python/Python312/python.exe'
$candidates += Get-ChildItem -LiteralPath 'C:/Program Files/Blender Foundation' -Recurse -Filter python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
$candidates += Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$command = Get-Command python -ErrorAction SilentlyContinue
if ($command) { $candidates += $command.Source }
$runtime = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (!(Test-Path -LiteralPath $candidate) -or $candidate -like '*WindowsApps*') { continue }
    & $candidate -c 'import sys; assert sys.version_info >= (3,8)' 2>$null
    if ($LASTEXITCODE -eq 0) { $runtime = $candidate; break }
}
if (!$runtime) { throw 'No usable Python found. Set PALM92_PYTHON to a Python 3.8+ executable.' }
& $runtime -m py_compile ./local_server.py
if ($LASTEXITCODE -ne 0) { throw 'Jarvis source validation failed. Server was not started.' }
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama -and !(Get-Process ollama -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $ollama.Source -ArgumentList 'serve' -WindowStyle Hidden
}
Write-Host "Starting Jarvis with $runtime"
& $runtime -u ./local_server.py
exit $LASTEXITCODE
