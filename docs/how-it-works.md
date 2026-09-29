# How it works

Notes from working this out, mostly so I do not have to rediscover any of it
after the next patch. Some of it was expensive to learn.

## Why every PC player gets Xbox prompts

Dungeons II uses Unreal's CommonUI for input. Its packed `DefaultGame.ini`
registers every controller profile the game owns for Windows:

```ini
[CommonInputPlatformSettings_Windows CommonInputPlatformSettings]
DefaultGamepadName=Generic
+ControllerData=.../GamepadPS4/CI_Gamepad_PS4.CI_Gamepad_PS4_C
+ControllerData=.../GamepadPS5/CI_Gamepad_PS5.CI_Gamepad_PS5_C
+ControllerData=.../GamepadXboxOne/CI_Gamepad_XboxOne.CI_Gamepad_XboxOne_C
...
```

Each profile carries a `GamepadName`. Read them out of the assets and the
problem is obvious:

| Profile | GamepadName |
| --- | --- |
| `CI_Gamepad_XboxOne` | `Generic` |
| `CI_Gamepad_PS5` | `PS5` |
| `CI_Gamepad_PS4` | `PS4` |
| `CI_Gamepad_Switch` | `Switch` |
| `CI_Gamepad_XSX` | `XSX` |

The Xbox profile is the one registered under `Generic`, and `Generic` is what
the game resolves a PC gamepad to. So everyone gets Xbox art.

## Things that look like the fix and are not

I burned most of a day on these. They all fail.

**Setting `DefaultGamepadName` in your user config.** The file at
`%LOCALAPPDATA%\Dungeons2\Saved\Config\Windows\Game.ini` is not consulted for
this setting. The game also rewrites its saved config on exit and deletes
anything it does not recognise, which makes it look like it worked and then
stopped.

**Setting it on the command line** with `-ini:Game:[...]:DefaultGamepadName=PS5`.
No effect.

**Setting it in the packed config.** This one genuinely applies, and you can
prove the override landed by disabling the startup movies in the same file and
watching them not play. The glyphs still do not change. The name the game asks
for is decided at runtime and this value is not it.

**Unregistering the Xbox profile** so nothing answers to `Generic`. You get no
prompts at all. The lookup is strict on the name and there is no fallback, not
even to `DefaultGamepadName`. Keyboard prompts keep working, which is how you
can tell the lookup itself is fine.

The conclusion is that the name is not a lever you can reach. What you can
change is what the profile it lands on draws.

## The approach that works

Every icon for a controller lives on one sprite sheet, and each prompt is a
rectangle cut out of it. Replace the Xbox sheet's pixels with PlayStation art
and the game keeps asking for the Xbox profile, quite happily, and draws
PlayStation buttons.

The catch is that the sheets do not share a layout:

| Sheet | Size | Grid |
| --- | --- | --- |
| Xbox | 504x504 | 6x6 |
| PlayStation | 504x504 | 6x6 |
| Switch | 588x588 | 7x7 |

Cells are 84x84 in all of them, but the icons sit in different cells. Xbox has
A at `(0,0)` and B at `(84,0)`; PlayStation has Circle at `(0,0)` and Cross at
`(84,0)`. Copy one sheet over the other and the game asks you to press Circle
to continue.

So the build reads each sprite's `SourceUV` out of its asset and copies cells
by name instead: Cross to where A was, Circle to where B was, L1 and R1 onto
the shoulders, and so on.

### Reading sprite coordinates

Paper2D sprites store `SourceUV` and `SourceDimension` as pairs of
double-precision floats. In these cooked assets they land at fixed offsets in
the `.uexp`:

- offsets 7 and 15: `SourceUV`
- offsets 23 and 31: `SourceDimension`

Unversioned property serialisation drops values equal to the default, so a
sprite at the sheet origin has no `SourceUV` at all and its
`SourceDimension` shows up at 7 and 15 instead. Two grid-sized values means
`(0,0)`, four means the first pair is the real UV.

### The texture payload

The sheets are `PF_B8G8R8A8`, uncompressed, single mip. The `.uexp` is a
151-byte header followed by raw BGRA pixels, and the arithmetic is exact:
`151 + 504 * 504 * 4 = 1016215`.

## Two things that will bite you

**Build the payload from a copy of a sheet the game already loads.** Compositing
the remapped icons onto a fresh empty canvas produces a texture that the D3D12
runtime rejects at load:

```
CreateCommittedResource(...) failed with error E_INVALIDARG
```

The bytes are the right length, the header is untouched, the pixels decode
fine as an image, and Pillow round-trips the payload exactly. I could not tell
you why it fails. Starting from a real payload and overwriting only whole
cells works, so that is what `build.py` does, and there is a comment there
saying not to change it.

**A bare `.pak` will not load.** This is an IoStore build, so a mod has to be a
`.utoc` / `.ucas` / `.pak` triplet sharing one name with a `_P` suffix, sitting
in `Dungeons/Content/Paks`. A lone `.pak` is ignored in silence, which is a
miserable thing to debug. Put something visible in every test build so you can
tell "the mod did nothing" apart from "the mod never loaded". Disabling the
startup movies in a config file inside the triplet works nicely for that.

## Still to do

The controller illustration on the System screen is a separate texture,
`T_Controller_XboxOne`, 212x148. The PlayStation equivalent is 244x164, so it
needs rescaling rather than a straight swap. A build that included it crashed
the same way as the empty-canvas texture, and I have not worked out whether
those two failures share a cause.
