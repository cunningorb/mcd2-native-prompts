# Minecraft Dungeons II: Native Controller Prompts

Dungeons II came out, I sat down with a DualSense, and the game spent the
whole evening telling me to press A. My controller does not have an A.
Every PC player gets Xbox prompts no matter what is plugged in.

I went in expecting to repaint a pile of button icons, because that is how
the old Minecraft Dungeons mods did it. I still have a DualShock 4 icon pak
sitting in that game's mods folder from years ago. None of that is needed
this time. The PlayStation icons are already sitting in your Windows
install, fully drawn and ready to go. The game just never picks them.

So this is a two line config file.

## What it changes

Dungeons II uses Unreal's CommonUI for input. Its Windows settings register
every controller profile the game owns, PS4, PS5, Switch, Xbox One and Xbox
Series, and then set the default gamepad to `Generic`. Here is the part that
made me laugh: the Xbox One profile is the one that claims the name
`Generic`. So the default quietly resolves to Xbox for everyone on PC, and
the PlayStation art it shipped with never gets a look in.

The fix is to name a different one.

```ini
[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]
DefaultGamepadName=PS5
```

That is the whole mod. No game files are modified, nothing is repacked, and
no artwork is redistributed. You are pointing the game at icons it already
gave you.

## Install

Right-click Start, open Terminal, paste this, press Enter:

```powershell
$v='PS5';$r=@("$env:LOCALAPPDATA\Dungeons2");foreach($k in @(Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter '*MinecraftDungeons2*' -EA 0)){$r+="$($k.FullName)\LocalCache\Local\Dungeons2"};$h='[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]';foreach($b in $r){$d="$b\Saved\Config\Windows";$f="$d\Game.ini";New-Item -ItemType Directory -Force $d|Out-Null;if(Test-Path $f){sp $f IsReadOnly $false};$l=@();if(Test-Path $f){$l=@(Get-Content $f|Where-Object{$_ -notmatch '^\s*DefaultGamepadName\s*='})};if($l -notcontains $h){if($l.Count -and $l[-1].Trim()){$l+=''};$l+=$h};$i=[array]::IndexOf($l,$h);$o=@();for($j=0;$j -lt $l.Count;$j++){$o+=$l[$j];if($j -eq $i){$o+="DefaultGamepadName=$v"}};Set-Content $f $o -Encoding UTF8;sp $f IsReadOnly $true;"Applied: $f"}
```

Restart the game. Done.

That works for Steam, Microsoft Store and Game Pass, and it does not care
where you installed the game, because the config lives in your user folder
instead of the game folder.

Prefer to do it by hand? Copy `variants/PS5/Game.ini` into this folder:

```
%LOCALAPPDATA%\Dungeons2\Saved\Config\Windows
```

Microsoft Store and Game Pass keep theirs somewhere less friendly:

```
%LOCALAPPDATA%\Packages\Microsoft.MinecraftDungeons2_8wekyb3d8bbwe\LocalCache\Local\Dungeons2\Saved\Config\Windows
```

Paste either one into the Explorer address bar and it will take you there.
If a `Game.ini` is already sitting in that folder, add the two lines to the
end of it rather than replacing the file.

Then right-click the file you just put there, open Properties, and tick
Read-only. Do not skip that part. The next section explains why.

## Why the file has to be read-only

Dungeons II keeps its user config in Unreal's newer diff based format, and
it rewrites those files when it shuts down. It only writes back the values
it believes it owns, and our section is not one of them, so on a clean exit
it deletes the whole file and you are looking at Xbox prompts again next
time you play.

This one caught me out. My first round of testing looked perfect, because I
had been killing the game from the task list rather than quitting it from
the menu, and killing it skips the config save entirely. The first time I
quit properly, the file was gone.

Marking it read-only stops the rewrite. The game still reads the value on
startup, finds it cannot write the file back afterwards, and carries on.
Nothing of yours lives in that file anyway. Your graphics and audio settings
are in `GameUserSettings.ini` next to it, which stays writable, so locking
this one costs you nothing.

## Uninstall

Run `uninstall.ps1`, or delete that `Game.ini` yourself. Windows will ask
you to confirm because the file is read-only, which is expected, say yes.
That really is all of it. You do not need to verify your files or reinstall
anything, because nothing outside your own config folder was ever touched.

## Other controllers

Swap the value, or grab the matching folder under `variants/`.

| Controller | Value |
| --- | --- |
| DualSense | `PS5` |
| DualShock 4 | `PS4` |
| Switch Pro and Joy-Con | `Switch` |
| Xbox Series X and S | `XSX` |
| Back to stock | `Generic` |

Only PS5 has been tested on real hardware, which was mine. The other three
use the exact same mechanism and I pulled their names straight out of the
game's own controller assets, so I expect them to be fine, but expecting and
knowing are different things. If you run one of them, I would love to hear
whether it worked.

The Joy-Con profiles both report themselves as `Switch`, so there is no way
to select left and right separately from here.

## Getting no prompts at all?

Then your controller is not reaching the game in the first place and this
mod cannot help, because there is nothing for it to relabel. Check that the
pad is actually awake. A DualSense that is paired over Bluetooth but asleep
still shows up in Windows while being completely invisible to the game,
which cost me a good ten minutes of staring at a title screen wondering why
nothing had changed. Toggling Steam Input for the game is worth a try too.

## How I found it

I pulled the config out of the game's packed data and read it. The answer
was sitting right there in `DefaultGame.ini` in plain text, which was a
little anticlimactic after I had talked myself into a long afternoon of
texture work.

If you want to confirm it yourself before trusting a config file from a
stranger on the internet, the values in the table above come from the
`GamepadName` property on each of the game's `CI_Gamepad_*` assets. Good
practice anyway.

## Notes

Cosmetic only, so it is safe in multiplayer. It lives in your user config
rather than the game's data, which means a game patch should not wipe it.
Built and tested against Dungeons II 1.1.1.0 on Unreal Engine 5.6.1.

If it breaks, or if you get it working on a controller I have not tried,
open an issue and tell me about it. I would rather hear it than not.
