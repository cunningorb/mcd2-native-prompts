#!/usr/bin/env python3
"""Builds the Nexus upload zips into dist/, and keeps README.md in sync.

Run this after changing anything in nexus/readme.template or the one-liner
below. It regenerates variants/*/Game.ini, the dist zips, and the install
command embedded in README.md so those three can never drift apart.
"""
import os, re, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER = "[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]"

# Literal braces are doubled because this goes through str.format().
ONELINER = r'''$v='{v}';$r=@("$env:LOCALAPPDATA\Dungeons2");foreach($k in @(Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter '*MinecraftDungeons2*' -EA 0)){{$r+="$($k.FullName)\LocalCache\Local\Dungeons2"}};$h='[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]';foreach($b in $r){{$d="$b\Saved\Config\Windows";$f="$d\Game.ini";New-Item -ItemType Directory -Force $d|Out-Null;if(Test-Path $f){{sp $f IsReadOnly $false}};$l=@();if(Test-Path $f){{$l=@(Get-Content $f|Where-Object{{$_ -notmatch '^\s*DefaultGamepadName\s*='}})}};if($l -notcontains $h){{if($l.Count -and $l[-1].Trim()){{$l+=''}};$l+=$h}};$i=[array]::IndexOf($l,$h);$o=@();for($j=0;$j -lt $l.Count;$j++){{$o+=$l[$j];if($j -eq $i){{$o+="DefaultGamepadName=$v"}}}};Set-Content $f $o -Encoding UTF8;sp $f IsReadOnly $true;"Applied: $f"}}'''

VARIANTS = [
    ("PS5-DualSense",  "PS5",    "PlayStation 5 / DualSense"),
    ("PS4-DualShock4", "PS4",    "PlayStation 4 / DualShock 4"),
    ("Switch-Pro",     "Switch", "Nintendo Switch"),
    ("XboxSeries",     "XSX",    "Xbox Series X|S"),
]


def one_liner(gamepad):
    line = ONELINER.format(v=gamepad)
    assert r"\Dungeons2" in line, "backslashes lost"
    assert "\n" not in line, "must stay on one line"
    assert line.startswith("$v='%s'" % gamepad), "wrong variant"
    return line


def main():
    template = open(os.path.join(HERE, "nexus", "readme.template"), encoding="utf-8").read()
    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)

    for name, gamepad, label in VARIANTS:
        line = one_liner(gamepad)
        readme = (template.replace("{{LABEL}}", label)
                          .replace("{{GAMEPAD}}", gamepad)
                          .replace("{{ONELINER}}", "     " + line))
        ini = "%s\nDefaultGamepadName=%s\n" % (HEADER, gamepad)

        out = os.path.join(dist, "MCD2-NativePrompts-%s.zip" % name)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Game.ini", ini.replace("\n", "\r\n"))
            z.writestr("README.txt", readme.replace("\n", "\r\n"))

        open(os.path.join(HERE, "variants", gamepad, "Game.ini"), "w",
             encoding="utf-8", newline="\r\n").write(ini)
        open(os.path.join(dist, "oneliner-%s.txt" % gamepad), "w",
             encoding="utf-8", newline="\r\n").write(line + "\n")
        print("built %-16s -> %s" % (name, os.path.basename(out)))

    # keep the command in README.md identical to the PS5 one we just shipped
    path = os.path.join(HERE, "README.md")
    text = open(path, encoding="utf-8").read()
    block = "```powershell\n%s\n```" % one_liner("PS5")
    new, n = re.subn(r"```powershell\n.*?\n```", lambda _: block,
                     text, count=1, flags=re.S)
    assert n == 1, "could not find the powershell block in README.md"
    if new != text:
        open(path, "w", encoding="utf-8", newline="\n").write(new)
        print("synced README.md install command")
    else:
        print("README.md already in sync")


if __name__ == "__main__":
    main()
