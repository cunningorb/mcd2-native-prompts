# Building

The mod is made out of the game's own artwork, so the build reads it straight
from your installation. None of it is committed here, which is why you cannot
build this from a clean checkout alone.

## What you need

**The game.** Any install works. The build looks in the usual Steam location
first, and you can point it somewhere else:

```
set MCD2_GAME_DIR=D:\Games\Minecraft Dungeons II
```

**Two tools**, dropped in `tools/`:

- [retoc](https://github.com/trumank/retoc) reads and writes the game's
  IoStore containers
- [repak](https://github.com/trumank/repak) handles the older `.pak` format,
  useful for poking around

`tools/` is gitignored. If the executables are on your PATH instead, the build
will find them there.

**Python** with Pillow, which is only used to write the preview images:

```
pip install pillow
```

**The container key.** Dungeons II encrypts its containers, so retoc needs the
key to read anything:

```
set MCD2_AES_KEY=0x...
```

The key is not in this repository and will not be. It is not ours to hand out,
and publishing a shipping game's container key mostly helps people rip assets.
It is not stored in any file on disk either, so the usual offline dumpers come
up empty on this build. It does exist in the game's memory once the containers
are mounted, which is where I got mine.

## Running it

```
python build.py                # both variants
python build.py PlayStation    # just one
```

You get, in `dist/`:

- `MCD2-PlayStationPrompts.zip` and `MCD2-SwitchPrompts.zip`, ready to upload
- `preview-PlayStation.png` and `preview-Switch.png`, the remapped sheets as
  images so you can check the icons landed in the right cells

Extracted assets are cached in `work/`. Delete that folder after a game patch,
otherwise you will rebuild against stale art.

The build refuses to run against an install that has a mod in its Paks folder,
including this one. Reading your own output back in as though it were the
game's art is an easy mistake to make and an invisible one to spot afterwards,
so move the `_P` files out and clear `work/` before building.

## Releasing

1. Bump `version` in `nexus/variants.json`
2. `python build.py`
3. Check the previews
4. Create a GitHub release and attach both zips
5. The workflow in `.github/workflows/nexus-release.yml` forwards them to Nexus

That last step only runs for variants with a `file_id` filled in. See the
comments in `nexus/variants.json`.
