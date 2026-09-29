<#
    Minecraft Dungeons II: Native Controller Prompts

    Removes the override. If the config file held nothing but this mod, the
    file goes too. Anything else you had in there is left where it was.
#>
$header = '[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]'

$roots = @("$env:LOCALAPPDATA\Dungeons2")
foreach ($pkg in @(Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter '*MinecraftDungeons2*' -ErrorAction SilentlyContinue)) {
    $roots += "$($pkg.FullName)\LocalCache\Local\Dungeons2"
}

$touched = $false
foreach ($root in $roots) {
    $file = "$root\Saved\Config\Windows\Game.ini"
    if (-not (Test-Path $file)) { continue }
    Set-ItemProperty -Path $file -Name IsReadOnly -Value $false

    $lines = @(Get-Content $file | Where-Object { $_ -notmatch '^\s*DefaultGamepadName\s*=' })

    # drop our section header too, if removing the key left it empty
    $at = [array]::IndexOf($lines, $header)
    if ($at -ge 0) {
        $hasKeys = $false
        for ($i = $at + 1; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^\s*\[') { break }
            if ($lines[$i].Trim()) { $hasKeys = $true; break }
        }
        if (-not $hasKeys) {
            $keep = @(); for ($i = 0; $i -lt $lines.Count; $i++) { if ($i -ne $at) { $keep += $lines[$i] } }
            $lines = $keep
        }
    }
    while ($lines.Count -and -not $lines[-1].Trim()) { $lines = $lines[0..($lines.Count - 2)] }

    if (($lines | Where-Object { $_.Trim() }).Count -eq 0) {
        Remove-Item $file
        Write-Host "Removed $file"
    } else {
        Set-Content -Path $file -Value $lines -Encoding UTF8
        Write-Host "Cleaned $file"
    }
    $touched = $true
}

if (-not $touched) { Write-Host "Nothing to remove." }
