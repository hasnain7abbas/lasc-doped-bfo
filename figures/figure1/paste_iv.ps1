# Paste the Fig. 1(c) I-V graph into Figure 1.pptx as an editable Origin object (Copy Page -> PasteSpecial OLE)
$PKG = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
function EnvOr($name, $default) { $v = [Environment]::GetEnvironmentVariable($name); if ($v) { $v } else { $default } }
$ORIGIN = EnvOr "ORIGIN_EXE" "C:\Program Files\OriginLab\Origin2024\Origin64.exe"
$WORK = EnvOr "LASC_WORK" "$PKG\work"
$T = "$PKG\origin_plots"
$F = EnvOr "LASC_FIG1" "$WORK\figure1"
$slot = Get-Content "$F\scripts\iv_slot.json" -Raw | ConvertFrom-Json
$cm = 28.3465

$p = Get-Process Origin64 -ErrorAction SilentlyContinue
if (-not $p) { Start-Process $ORIGIN; Start-Sleep -Seconds 25 }
$app = New-Object -ComObject Origin.ApplicationSI
New-Item -ItemType Directory -Force "$WORK\jobs" | Out-Null
$jp = "$WORK\jobs\job_fig1c.json"
@{ path = "$F/origin/IV_bipolar_Fig1c.opju".Replace('\', '/'); graph = "IVbip1" } | ConvertTo-Json | Set-Content $jp -Encoding UTF8
$lg = $jp.Replace('.json', '.log'); if (Test-Path $lg) { Remove-Item $lg }
$null = $app.Execute("string jobpath`$ = `"$($jp.Replace('\','/'))`"; run -pyf `"$($T.Replace('\','/'))/copy_one.py`";")
Start-Sleep -Seconds 2
if (-not ((Test-Path $lg) -and ((Get-Content $lg -Raw) -match 'OK'))) { "COPY FAILED"; Get-Content $lg; exit 1 }

$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("$F\Figure 1.pptx", $false, $false, $false)
$s = $pres.Slides(1)
$sh = $null
for ($i = 1; $i -le 5 -and -not $sh; $i++) { try { $sh = $s.Shapes.PasteSpecial(10).Item(1) } catch { Start-Sleep -Milliseconds 900 } }
if (-not $sh) { "PASTE FAILED"; $pres.Close(); exit 1 }
$sh.Name = "Fig1c IV (Origin)"
$sh.LockAspectRatio = -1
$sh.PictureFormat.CropTop = $sh.Height * 0.075     # empty band left by the removed slide title
$sh.Height = $slot.height_cm * $cm
$maxW = ($slot.right_cm - $slot.left_cm) * $cm
if ($sh.Width -gt $maxW) { $sh.Width = $maxW }
$sh.Left = $slot.left_cm * $cm + (($maxW - $sh.Width) / 2)
$sh.Top = $slot.top_cm * $cm + (($slot.height_cm * $cm - $sh.Height) / 2)
"pasted: {0:N2} x {1:N2} cm" -f ($sh.Width / $cm), ($sh.Height / $cm)
$pres.Save()
$s.Export("$F\Figure 1 preview.png", "PNG", 2067)
$pres.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
