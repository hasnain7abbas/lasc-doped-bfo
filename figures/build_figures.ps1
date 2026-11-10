# Build the paper figures from spec.json:
#   Origin panels -> Copy Page (copy_one.py) -> PasteSpecial OLE (editable), cropped and scaled
#   pulse schemes -> native groups copied from "La-Sc figures (Origin).pptx", text and lines scaled with them
#   panel letters -> Times New Roman bold
# usage: build_figures.ps1 [-only "Figure 2,Figure 5"]
param([string]$only = "")
$ErrorActionPreference = "Stop"
$PKG = Split-Path $PSScriptRoot -Parent
function EnvOr($name, $default) { $v = [Environment]::GetEnvironmentVariable($name); if ($v) { $v } else { $default } }
$ORIGIN = EnvOr "ORIGIN_EXE" "C:\Program Files\OriginLab\Origin2024\Origin64.exe"
$WORK = EnvOr "LASC_WORK" "$PKG\work"
$T = "$PKG\origin_plots"                                        # folder of copy_one.py
$R = EnvOr "LASC_PAPER_FIG" "$WORK\paper_figures"              # output; spec.json is read from $R\scripts
$DECK = EnvOr "LASC_DECK" "$WORK\origin_figures\La-Sc figures (Origin).pptx"   # deck with the pulse-scheme groups
$cm = 28.3465
$spec = Get-Content "$R\scripts\spec.json" -Raw | ConvertFrom-Json
if ($only) { $want = $only.Split(",") | ForEach-Object { $_.Trim() }; $spec = $spec | Where-Object { $want -contains $_.name } }

if (-not (Get-Process Origin64 -ErrorAction SilentlyContinue)) { Start-Process $ORIGIN; Start-Sleep -Seconds 25 }
$app = New-Object -ComObject Origin.ApplicationSI
New-Item -ItemType Directory -Force "$WORK\jobs" | Out-Null
$script:job = 0
function Copy-Graph($path, $graph) {
    for ($try = 1; $try -le 3; $try++) {
        $script:job++
        $jp = "$WORK\jobs\pf_$($script:job).json"
        @{ path = $path; graph = $graph } | ConvertTo-Json | Set-Content $jp -Encoding UTF8
        $null = $app.Execute("string jobpath`$ = `"$($jp.Replace('\','/'))`"; run -pyf `"$($T.Replace('\','/'))/copy_one.py`";")
        $lg = $jp.Replace('.json', '.log')
        if ((Test-Path $lg) -and ((Get-Content $lg -Raw) -match 'OK')) { Start-Sleep -Milliseconds 900; return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}
function Paste-On($s) {
    for ($try = 1; $try -le 6; $try++) { try { return $s.Shapes.PasteSpecial(10).Item(1) } catch { Start-Sleep -Milliseconds 900 } }
    return $null
}
function Scale-Group($g, $f) {
    foreach ($it in $g.GroupItems) {
        if ($it.HasTextFrame -and $it.TextFrame.HasText) {
            $tr = $it.TextFrame.TextRange
            for ($i = 1; $i -le $tr.Runs().Count; $i++) { $r = $tr.Runs($i); $r.Font.Size = [Math]::Max(5, $r.Font.Size * $f) }
            $it.TextFrame.MarginLeft = 0; $it.TextFrame.MarginRight = 0; $it.TextFrame.MarginTop = 0; $it.TextFrame.MarginBottom = 0
        }
        try { if ($it.Line.Visible) { $it.Line.Weight = [Math]::Max(0.5, $it.Line.Weight * $f) } } catch {}
    }
}

$pp = New-Object -ComObject PowerPoint.Application
$deck = $pp.Presentations.Open($DECK, $true, $false, $false)
$schemes = @{}
foreach ($sl in $deck.Slides) { foreach ($sh in $sl.Shapes) { if ($sh.Name -like "Scheme_*" -and -not $schemes.ContainsKey($sh.Name)) { $schemes[$sh.Name] = $sh } } }

foreach ($f in $spec) {
    "== $($f.name)"
    $pres = $pp.Presentations.Add($false)
    $pres.PageSetup.SlideWidth = $f.width * $cm
    $pres.PageSetup.SlideHeight = $f.height * $cm
    $s = $pres.Slides.Add(1, 12)
    $script:ptScale = 0.3
    foreach ($it in $f.items) {
        if ($it.kind -eq "origin") {
            if (-not (Copy-Graph $it.path $it.graph)) { "  COPY FAILED $($it.name)"; continue }
            $sh = Paste-On $s
            if (-not $sh) { "  PASTE FAILED $($it.name)"; continue }
            $sh.Name = $it.name
            $sh.LockAspectRatio = -1
            $W0 = $sh.Width; $H0 = $sh.Height
            $sh.PictureFormat.CropLeft = $it.crop[0] * $W0
            $sh.PictureFormat.CropTop = $it.crop[1] * $H0
            $sh.PictureFormat.CropRight = $it.crop[2] * $W0
            $sh.PictureFormat.CropBottom = $it.crop[3] * $H0
            $sh.Width = $it.width * $cm
            $script:ptScale = ($it.width * $cm / (1 - $it.crop[0] - $it.crop[2])) / $W0     # printed / native page width
            $sh.Left = $it.left * $cm; $sh.Top = $it.top * $cm
            "  {0,-26} {1:N2} x {2:N2} cm" -f $it.name, ($sh.Width / $cm), ($sh.Height / $cm)
        }
        elseif ($it.kind -eq "scheme") {
            $src = $schemes[$it.name]
            if (-not $src) { "  NO SCHEME $($it.name)"; continue }
            $src.Copy(); Start-Sleep -Milliseconds 500
            $g = $s.Shapes.Paste().Item(1)
            $g.LockAspectRatio = -1
            # one factor for geometry, text and lines keeps the deck's proportions (no text running into pulses)
            $f0 = [Math]::Min($it.width * $cm / $g.Width, $it.height * $cm / $g.Height)
            $W1 = $g.Width * $f0
            Scale-Group $g $f0
            # the min-5-pt font rule makes the arrow labels relatively larger than in the deck: move them off the arrowheads
            foreach ($gi in $g.GroupItems) {
                if ($gi.HasTextFrame -and $gi.TextFrame.HasText) {
                    $tt = $gi.TextFrame.TextRange.Text
                    try {
                        if ($tt -match 'pulses \(potentiation\)') { $gi.IncrementTop([single](-0.5 * $gi.Height)) }
                        elseif ($tt -match 'pulses \(depression\)') { $gi.IncrementTop([single](0.4 * $gi.Height)) }
                    } catch { "  label nudge skipped: $($_.Exception.Message)" }
                }
            }
            $g.LockAspectRatio = -1
            $g.Width = $W1
            $g.Left = $it.left * $cm + ($it.width * $cm - $g.Width) / 2
            $g.Top = $it.top * $cm + ($it.height * $cm - $g.Height) / 2
            "  {0,-26} scheme x{1:N2}" -f $it.name, $f0
        }
        else {
            $tb = $s.Shapes.AddTextbox(1, $it.left * $cm, $it.top * $cm, 1.2 * $cm, 0.45 * $cm)
            $tb.TextFrame.MarginLeft = 0; $tb.TextFrame.MarginTop = 0; $tb.TextFrame.MarginRight = 0; $tb.TextFrame.MarginBottom = 0
            $tb.TextFrame.WordWrap = 0
            $tr = $tb.TextFrame.TextRange; $tr.Text = $it.text
            $tr.Font.Name = "Times New Roman"; $tr.Font.Bold = -1; $tr.Font.Size = 10; $tr.Font.Color.RGB = 0
            $tb.Name = "letter " + $it.text
        }
    }
    if (Test-Path $f.pptx) { Remove-Item $f.pptx -Force }
    $pres.SaveAs($f.pptx)
    $s.Export($f.png, "PNG", 2067)
    $pres.Close()
}
$deck.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
"ALL DONE"
