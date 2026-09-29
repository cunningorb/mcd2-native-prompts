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

Drop these three files into your game's Paks folder:

    Dungeons-Windows_P.utoc
    Dungeons-Windows_P.ucas
    Dungeons-Windows_P.pak

On Steam that folder is here:

    ...\steamapps\common\Minecraft Dungeons II\Dungeons\Content\Paks

On Microsoft Store and Game Pass, open the game's install location and look
for the same Dungeons\Content\Paks folder inside it.

All three files have to go in together and keep their names. They are one
container split across three files, and the game ignores an incomplete set.

Start the game. Done.

## Uninstall

Delete those three files. Nothing else was touched, so there is nothing else
to undo. Verifying your game files through Steam will also remove them, which
is worth knowing if you ever wonder where the mod went.

## What it actually changes

One texture. The game keeps every button icon for a given controller on a
single sprite sheet, and each on-screen prompt is a rectangle cut out of that
sheet. This mod hands the Xbox sheet the PlayStation artwork, with every icon
moved to the coordinate the Xbox prompt expects to find it at.

That last part is the whole job. The two sheets are both 504 by 504 with the
same 84 pixel cells, but the icons sit in different cells. Copy one sheet over
the other and you get PlayStation icons in the wrong places, which looks like
the game asking you to press Circle to continue. Every icon is remapped by
name instead, so Cross lands where A was, Circle where B was, L1 and R1 on the
shoulders, and so on.

## Heads up

The prompts change for every controller, not just PlayStation ones. The game
never learns what you have plugged in, so if you swap to an Xbox pad you will
still see PlayStation prompts until you remove the mod. That is the tradeoff
for a fix this small, and it is the same one the old Dungeons mods made.

The controller picture on the System screen still shows an Xbox pad. That is a
separate texture and it is on my list.

## Why the game gets this wrong

For the curious. Dungeons II uses Unreal's CommonUI for input, and its Windows
settings register every controller profile the game owns, PS4, PS5, Switch,
Xbox One and Xbox Series. Then it sets the default gamepad name to Generic.

Here is the part that made me laugh: the Xbox One profile is the one that
claims the name Generic. So every PC player resolves to Xbox, whatever they
are holding.

I spent a long time trying to make the game ask for a different profile
instead. It will not. The name it asks for is decided at runtime and none of
the obvious settings move it, and if you unregister the Xbox profile so
nothing answers to Generic, you get no prompts at all rather than a fallback.
Once that was clear, the answer was to stop arguing with the lookup and change
what the Xbox profile draws.

## Other controllers

There is a Switch version too. Nintendo needed the same treatment rather than
a straight copy, because that sheet is 588 by 588 in a seven by seven grid
instead of six by six, so nothing lines up on its own.

Only the PlayStation version has been tested on real hardware, which was mine.
The Switch one is built the same way from the game's own Switch icons, and I
have eyeballed the result, but eyeballing and playing are different things.
Tell me in the comments if you run it.

On Switch the buttons are mapped by what they do, not where they sit. Nintendo
puts A and B in the opposite corners from Xbox, so confirm shows as A and back
shows as B, which is what your hands expect even though the letters have moved.

## Compatibility

Cosmetic only, so it is safe in multiplayer. Built against Dungeons II 1.1.1.0
on Unreal Engine 5.6.1. A game patch that touches the icon sheets will need a
rebuild, so if prompts go strange after an update, pull the files out and give
me a shout.
