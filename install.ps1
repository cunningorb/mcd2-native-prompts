<#
    Minecraft Dungeons II: Native Controller Prompts

    Usage:
        .\install.ps1                 installs the PS5 (DualSense) prompts
        .\install.ps1 -Variant PS4    DualShock 4
        .\install.ps1 -Variant Switch Switch Pro / Joy-Con
        .\install.ps1 -Variant XSX    Xbox Series X|S

    Writes a two line override into your Dungeons II user config. Finds the
    Steam location and the Microsoft Store / Game Pass location on its own,
    and leaves any other settings in that file alone.
#>
param([ValidateSet('PS5','PS4','Switch','XSX','Generic')][string]$Variant = 'PS5')

$header = '[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]'

$roots = @("$env:LOCALAPPDATA\Dungeons2")
foreach ($pkg in @(Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter '*MinecraftDungeons2*' -ErrorAction SilentlyContinue)) {
    $roots += "$($pkg.FullName)\LocalCache\Local\Dungeons2"
}

foreach ($root in $roots) {
    $dir  = "$root\Saved\Config\Windows"
    $file = "$dir\Game.ini"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null

    $lines = @()
    if (Test-Path $file) {
        $lines = @(Get-Content $file | Where-Object { $_ -notmatch '^\s*DefaultGamepadName\s*=' })
    }
    if ($lines -notcontains $header) {
        if ($lines.Count -and $lines[-1].Trim()) { $lines += '' }
        $lines += $header
    }

    $at = [array]::IndexOf($lines, $header)
    $out = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $out += $lines[$i]
        if ($i -eq $at) { $out += "DefaultGamepadName=$Variant" }
    }

    Set-Content -Path $file -Value $out -Encoding UTF8
    Write-Host "Set $Variant prompts in $file"
}

Write-Host "Restart the game to see it."
