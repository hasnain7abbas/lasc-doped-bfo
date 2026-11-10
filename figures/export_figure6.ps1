# Export Figure 6.pptx to previews\Figure 6.png
$PKG = Split-Path $PSScriptRoot -Parent
function EnvOr($name, $default) { $v = [Environment]::GetEnvironmentVariable($name); if ($v) { $v } else { $default } }
$ORIGIN = EnvOr "ORIGIN_EXE" "C:\Program Files\OriginLab\Origin2024\Origin64.exe"
$WORK = EnvOr "LASC_WORK" "$PKG\work"
$R = EnvOr "LASC_PAPER_FIG" "$WORK\paper_figures"
$f = "$R\Figure 6.pptx"
$pp = New-Object -ComObject PowerPoint.Application
$p = $pp.Presentations.Open($f, $true, $false, $false)
$p.Slides(1).Export("$R\previews\Figure 6.png", "PNG", 2067)
$p.Close(); "exported"
