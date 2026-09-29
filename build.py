#!/usr/bin/env python3
"""Build the Minecraft Dungeons II controller prompt packages.

The mod is made entirely out of the game's own artwork, so this reads the
assets out of your installation every time it runs. Nothing from the game is
kept in this repository.

You need:
  - a Minecraft Dungeons II install
  - retoc and repak in tools/ (see docs/building.md)
  - the container key in the MCD2_AES_KEY environment variable

Then:
  python build.py                # everything
  python build.py PlayStation    # one variant

Output lands in dist/.
"""
import glob, json, os, shutil, struct, subprocess, sys, zipfile
from PIL import Image

HERE  = os.path.dirname(os.path.abspath(__file__))
WORK  = os.path.join(HERE, "work")
DIST  = os.path.join(HERE, "dist")
TOOLS = os.path.join(HERE, "tools")

# the Xbox sheet is the one the game actually draws from, so it is the target
TARGET_DIR  = "Dungeons/Content/Spicewood/Core/Platform/Input/CommonUIInput/GamepadXboxOne"
TARGET_NAME = "T_UI_Icon_SpriteSheet_Xbox"
W, CELL, BPP, HDR = 504, 84, 4, 151

VARIANTS = {
    "PlayStation": dict(
        folder="GamepadPS4", prefix="Sprite_UI_P_PS4-",
        sheet=("GamepadPS4", "T_UI_Icon_SpriteSheet_PS5"),
        rename={"A": "Cross", "B": "Circle", "X": "Square", "Y": "Triangle",
                "LB": "L1", "LT": "L2", "RB": "R1", "RT": "R2",
                "View": "Share", "Menu": "Options"},
        label="PlayStation", tested=True),
    "Switch": dict(
        folder="GamepadSwitch", prefix="Sprite_UI_P_NS-",
        sheet=("GamepadSwitch", "T_UI_Icon_SpriteSheet_Switch"),
        rename={"LB": "L", "LT": "ZL", "RB": "R", "RT": "ZR",
                "View": "Minus", "Menu": "Plus"},
        label="Nintendo Switch", tested=False),
}

STEAM_DEFAULT = r"C:\Program Files (x86)\Steam\steamapps\common\Minecraft Dungeons II"


def die(msg):
    sys.exit("error: " + msg)


def game_paks():
    root = os.environ.get("MCD2_GAME_DIR", STEAM_DEFAULT)
    paks = os.path.join(root, "Dungeons", "Content", "Paks")
    if not os.path.isdir(paks):
        die("no Paks folder at %s\n       set MCD2_GAME_DIR to your install" % paks)

    # Building against a modded install reads our own output back in as if it
    # were the game's art, and the mistake is invisible in the result.
    mods = sorted(os.path.basename(p) for p in glob.glob(os.path.join(paks, "*_P.*")))
    if mods:
        die("this install has a mod in it:\n       %s\n"
            "       move those out of the Paks folder and delete work/ first,"
            " otherwise the build reads its own output back in"
            % "\n       ".join(mods))
    return paks


def tool(name):
    p = os.path.join(TOOLS, name + ".exe")
    return p if os.path.exists(p) else name


def extract(paks, key):
    """Pull the sprite and sheet assets out of the game into work/."""
    out = os.path.join(WORK, "assets")
    if os.path.isdir(out):
        return out
    os.makedirs(WORK, exist_ok=True)
    for filt in ("Sprite_UI_P_", "T_UI_Icon_SpriteSheet"):
        subprocess.run([tool("retoc"), "-a", key, "to-legacy", "--version", "UE5_6",
                        "--no-shaders", "-f", filt, paks, out],
                       check=True, stdout=subprocess.DEVNULL)
    return out


def uv_of(path):
    """SourceUV for a Paper2D sprite. It is omitted when it is (0,0), so a
    two-value read means the sprite sits at the sheet origin."""
    d = open(path, "rb").read()

    def dbl(off):
        v = struct.unpack_from("<d", d, off)[0]
        return v if (v == v and 0 <= v <= 4096 and abs(v - round(v)) < 1e-9) else None

    a, b, c, e = dbl(7), dbl(15), dbl(23), dbl(31)
    if c == CELL and e == CELL:
        return (int(a), int(b))
    if a == CELL and b == CELL:
        return (0, 0)
    die("could not read sprite coordinates from %s" % os.path.basename(path))


def sprites(assets, folder, prefix):
    base = os.path.join(assets, *TARGET_DIR.split("/")[:-1], folder)
    found = glob.glob(os.path.join(base, prefix + "*.uexp"))
    if not found:
        die("no sprites found in %s" % base)
    return {os.path.basename(p)[len(prefix):-5]: uv_of(p) for p in found}


def sheet(assets, folder, name):
    p = os.path.join(assets, *TARGET_DIR.split("/")[:-1], folder, name + ".uexp")
    d = open(p, "rb").read()
    sx, sy = struct.unpack_from("<ii", d, 8)
    return d[:HDR], d[HDR:], sx, sy


def build(tag, assets):
    """Remap one variant's icons into the coordinates the Xbox sprites read.

    The payload starts as a copy of a sheet the game already loads, and only
    whole cells are overwritten. Compositing onto an empty canvas instead
    produces a texture the D3D12 runtime rejects at load, so do not do that.
    """
    v = VARIANTS[tag]
    xb = sprites(assets, "GamepadXboxOne", "Sprite_UI_P_XB1-")
    tgt = sprites(assets, v["folder"], v["prefix"])
    base_hdr, base_px, _, _ = sheet(assets, "GamepadPS4", "T_UI_Icon_SpriteSheet_PS5")
    _, src, sw, _ = sheet(assets, *v["sheet"])

    dst = bytearray(base_px)
    for name, (dx, dy) in sorted(xb.items()):
        want = v["rename"].get(name, name)
        if want not in tgt:
            die("%s has no counterpart for %s" % (tag, name))
        sx, sy = tgt[want]
        for row in range(CELL):
            so = ((sy + row) * sw + sx) * BPP
            do = ((dy + row) * W + dx) * BPP
            dst[do:do + CELL * BPP] = src[so:so + CELL * BPP]

    payload = base_hdr + bytes(dst)
    stage = os.path.join(WORK, "stage", tag, *TARGET_DIR.split("/"))
    os.makedirs(stage, exist_ok=True)
    shutil.copyfile(os.path.join(assets, *TARGET_DIR.split("/"), TARGET_NAME + ".uasset"),
                    os.path.join(stage, TARGET_NAME + ".uasset"))
    open(os.path.join(stage, TARGET_NAME + ".uexp"), "wb").write(payload)

    img = Image.frombytes("RGBA", (W, W), bytes(dst))
    b, g, r, a = img.split()
    bg = Image.new("RGBA", (W, W), (30, 30, 40, 255))
    bg.alpha_composite(Image.merge("RGBA", (r, g, b, a)))
    os.makedirs(DIST, exist_ok=True)
    bg.convert("RGB").save(os.path.join(DIST, "preview-%s.png" % tag))
    print("  %-12s %d icons remapped from a %dx%d sheet" % (tag, len(xb), sw, sw))
    return os.path.join(WORK, "stage", tag)


def package(tag, staged, key, version):
    out = os.path.join(DIST, tag)
    os.makedirs(out, exist_ok=True)
    subprocess.run([tool("retoc"), "-a", key, "to-zen", "--version", "UE5_6",
                    staged, os.path.join(out, "Dungeons-Windows_P.utoc")],
                   check=True, stdout=subprocess.DEVNULL)

    v = VARIANTS[tag]
    tmpl = open(os.path.join(HERE, "nexus", "readme.template"), encoding="utf-8").read()
    untested = ("\nThis version has not been tested on real hardware. It is built the same\n"
                "way as the PlayStation one, from the game's own icons, and checked by eye.\n"
                "Please say how you get on.\n")
    body = (tmpl.replace("{{LABEL}}", v["label"])
                .replace("{{VERSION}}", version)
                .replace("{{TESTED}}", "" if v["tested"] else untested))
    open(os.path.join(out, "README.txt"), "w", encoding="utf-8", newline="\r\n").write(body)

    zpath = os.path.join(DIST, "MCD2-%sPrompts.zip" % tag)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("Dungeons-Windows_P.utoc", "Dungeons-Windows_P.ucas",
                  "Dungeons-Windows_P.pak", "README.txt"):
            z.write(os.path.join(out, f), f)
    print("  %-12s -> %s (%d KB)" % (tag, os.path.basename(zpath),
                                     os.path.getsize(zpath) // 1024))
    return zpath


def main():
    key = os.environ.get("MCD2_AES_KEY")
    if not key:
        die("set MCD2_AES_KEY to the game's container key (see docs/building.md)")

    meta = json.load(open(os.path.join(HERE, "nexus", "variants.json"), encoding="utf-8"))
    version = meta.get("version", "1.0")

    wanted = sys.argv[1:] or list(VARIANTS)
    for t in wanted:
        if t not in VARIANTS:
            die("unknown variant %r, expected one of %s" % (t, ", ".join(VARIANTS)))

    paks = game_paks()
    print("reading assets from %s" % paks)
    assets = extract(paks, key)
    print("building:")
    for t in wanted:
        package(t, build(t, assets), key, version)
    print("\ndone, packages are in dist/")


if __name__ == "__main__":
    main()
