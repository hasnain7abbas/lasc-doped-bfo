# Paste the Origin panels of Fig. 6 (Copy Page, editable OLE) into Figure 6.pptx: (c) LUT_check, (d) Accuracy_vs_epoch,
# cropped/sized from fig6_geom.json (fig6_geom.py); save and export previews\Figure 6.png.
# usage: python figures/build_figure6_network.py --hidden 200; python figures/fig6_geom.py; powershell -File figures/paste_fig6.ps1
$ErrorActionPreference = "Stop"
$PKG = Split-Path $PSScriptRoot -Parent
function EnvOr($name, $default) { $v = [Environment]::GetEnvironmentVariable($name); if ($v) { $v } else { $default } }
$ORIGIN = EnvOr "ORIGIN_EXE" "C:\Program Files\OriginLab\Origin2024\Origin64.exe"
$WORK = EnvOr "LASC_WORK" "$PKG\work"
$T = "$PKG\origin_plots"                                        # folder of copy_one.py
$R = EnvOr "LASC_PAPER_FIG" "$WORK\paper_figures"
$cm = 28.3465
$panels = Get-Content "$PSScriptRoot\fig6_geom.json" -Raw | ConvertFrom-Json

if (-not (Get-Process Origin64 -ErrorAction SilentlyContinue)) { Start-Process $ORIGIN; Start-Sleep -Seconds 25 }
$app = New-Object -ComObject Origin.ApplicationSI
New-Item -ItemType Directory -Force "$WORK\jobs" | Out-Null
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("$R\Figure 6.pptx", $false, $false, $false)
$s = $pres.Slides(1)
$n = 0
foreach ($g in $panels) {
    $ok = $false
    for ($try = 1; $try -le 3 -and -not $ok; $try++) {
        $n++
        $jp = "$WORK\jobs\fig6_$n.json"
        @{ path = $g.path; graph = $g.graph } | ConvertTo-Json | Set-Content $jp -Encoding UTF8
        $null = $app.Execute("string jobpath`$ = `"$($jp.Replace('\','/'))`"; run -pyf `"$($T.Replace('\','/'))/copy_one.py`";")
        $lg = $jp.Replace('.json', '.log')
        if ((Test-Path $lg) -and ((Get-Content $lg -Raw) -match 'OK')) { $ok = $true; Start-Sleep -Milliseconds 900 } else { Start-Sleep -Seconds 2 }
    }
    if (-not $ok) { throw "Origin Copy Page failed for $($g.name)" }
    foreach ($old in @($s.Shapes | Where-Object { $_.Name -eq $g.name })) { $old.Delete() }
    $sh = $null
    for ($try = 1; $try -le 6 -and -not $sh; $try++) { try { $sh = $s.Shapes.PasteSpecial(10).Item(1) } catch { Start-Sleep -Milliseconds 900 } }
    if (-not $sh) { throw "paste failed for $($g.name)" }
    $sh.Name = $g.name
    $sh.LockAspectRatio = -1
    $W0 = $sh.Width; $H0 = $sh.Height
    $sh.PictureFormat.CropLeft = $g.crop[0] * $W0
    $sh.PictureFormat.CropTop = $g.crop[1] * $H0
    $sh.PictureFormat.CropRight = $g.crop[2] * $W0
    $sh.PictureFormat.CropBottom = $g.crop[3] * $H0
    $sh.Width = $g.width * $cm
    $sh.Left = $g.left * $cm; $sh.Top = $g.top * $cm
    "{0,-20} {1:N2} x {2:N2} cm at ({3:N2}, {4:N2})" -f $g.name, ($sh.Width / $cm), ($sh.Height / $cm), ($sh.Left / $cm), ($sh.Top / $cm)
}
$pres.Save()
$s.Export("$R\previews\Figure 6.png", "PNG", 2067)
$pres.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
"DONE"
