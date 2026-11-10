param([string]$py, [switch]$keep)
$ORIGIN = $env:ORIGIN_EXE; if (-not $ORIGIN) { $ORIGIN = "C:\Program Files\OriginLab\Origin2024\Origin64.exe" }
$env:LASC_PKG = Split-Path $PSScriptRoot -Parent   # read by the Origin scripts when __file__ is undefined
$log = [IO.Path]::ChangeExtension($py, '.log')
if (Test-Path $log) { Remove-Item $log -Force }
$p = Get-Process Origin64 -ErrorAction SilentlyContinue
if (-not $p) { Start-Process $ORIGIN; Start-Sleep -Seconds 25 }
$app = New-Object -ComObject Origin.ApplicationSI
$pp = $py.Replace('\','/')
$ok = $app.Execute("run -pyf `"$pp`";")
"Execute returned: $ok"
if (Test-Path $log) { Get-Content $log -Encoding UTF8 }
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
