# Minecraft Dungeons II: Native Controller Prompts

I sat down with Dungeons II and a DualSense, and the game spent the whole
evening telling me to press A. My controller does not have an A. Every PC
player gets Xbox prompts no matter what is plugged in. This does not pass the
significant other / kid check.

I went in expecting to repaint a pile of button icons, because that is how the
old Minecraft Dungeons mods did it. Turns out nobody needs to draw anything.
The PlayStation icons are already sitting in your Windows install, fully drawn
and ready to go. The game just never picks them.

So this mod does not add art. It takes the icons the game already ships and
puts them where the game is already looking.

## Install

Grab a zip from [releases](../../releases) and put all three files into your
game's Paks folder:

```
Dungeons-Windows_P.utoc
Dungeons-Windows_P.ucas
Dungeons-Windows_P.pak
```

On Steam:

```
...\steamapps\common\Minecraft Dungeons II\Dungeons\Content\Paks
```

On Microsoft Store and Game Pass, open the game's install location and look
for the same `Dungeons\Content\Paks` folder inside it.

Keep all three together and do not rename them. They are one container split
across three files, and the game ignores an incomplete set.

Start the game. That is it.

## Uninstall

Delete those three files. Nothing else was touched, so there is nothing else
to undo. Verifying your game files through Steam also removes them, which is
worth knowing if the mod ever seems to vanish on its own.

## Versions

| | Tested |
| --- | --- |
| PlayStation | yes, on a DualSense, mine |
| Nintendo Switch | not on hardware |

They use the same three filenames, so they replace each other rather than
stacking.

The Switch one needed real work rather than a copy of the PlayStation
approach, because that sheet is 588 by 588 in a seven by seven grid against
Xbox's 504 by 504 six by six. Nothing lines up on its own. Buttons are mapped
by what they do rather than where they sit, so confirm shows as A and back
shows as B, which is what your hands expect even though Nintendo puts those
letters in the opposite corners.

## Worth knowing

The prompts change for every controller, not just the one you picked. The game
never learns what you have plugged in, so an Xbox pad will still show
PlayStation buttons until you remove the files. That is the tradeoff for a fix
this small, and it is the same one the old Dungeons mods made.

The controller picture on the System screen still shows an Xbox pad. Separate
texture, later version.

Cosmetic only, so it is safe in multiplayer. Built against Dungeons II 1.1.1.0
on Unreal Engine 5.6.1.

## Why the game gets this wrong

Short version: Unreal's CommonUI registers every controller profile the game
owns, then sets the default gamepad name to `Generic`, and the Xbox profile is
the one that claims that name. So everyone on PC resolves to Xbox.

You cannot fix it by asking for a different name. I tried every way there is
and none of them move it. What you can do is change what that profile draws.

The long version, including the several approaches that look right and are
not, is in [docs/how-it-works.md](docs/how-it-works.md). Read that one before
the next game patch breaks something.

## Building

The mod is made out of the game's own artwork, so the build reads it out of
your installation and none of it lives here. See
[docs/building.md](docs/building.md).

```
python build.py
```

## Publishing

`nexus/` holds the mod page description, the readme that ships inside each
zip, and `variants.json` with the Nexus file ids.

Releases go up through [the official Nexus upload
action](https://github.com/Nexus-Mods/upload-action). The build cannot run in
CI, because the game's assets are not here and have no business being in a CI
runner, so the flow is: build locally, attach the zips to a GitHub release,
and the workflow forwards them to the mod page.

The upload API adds a version to a file that already exists, so each variant
has to be uploaded by hand once before any of it is automatic. Fill in
`mod_id` and the `file_id` values in `nexus/variants.json` afterwards, add
`NEXUSMODS_API_KEY` as a repository secret, and it runs itself from then on.
Variants without a `file_id` are skipped with a warning rather than failing
the run.
