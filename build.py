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

INPUT = "/Game/Spicewood/Core/Platform/Input/CommonUIInput"
INPUTMAP = "/OreUI/UI/Widget/InputMap"

VARIANTS = {
    "PlayStation": dict(
        folder="GamepadPS4", prefix="Sprite_UI_P_PS4-",
        sheet=("GamepadPS4", "T_UI_Icon_SpriteSheet_PS5"),
        rename={"A": "Cross", "B": "Circle", "X": "Square", "Y": "Triangle",
                "LB": "L1", "LT": "L2", "RB": "R1", "RT": "R2",
                "View": "Share", "Menu": "Options"},
        icon=INPUT + "/GamepadPS5/T_UI-Controller-PS5.T_UI-Controller-PS5",
        inputmap=INPUTMAP + "/PlayStationScreens/W_InputMapPlayStation.W_InputMapPlayStation_C",
        label="PlayStation", tested=True),
    "Switch": dict(
        folder="GamepadSwitch", prefix="Sprite_UI_P_NS-",
        sheet=("GamepadSwitch", "T_UI_Icon_SpriteSheet_Switch"),
        rename={"LB": "L", "LT": "ZL", "RB": "R", "RT": "ZR",
                "View": "Minus", "Menu": "Plus"},
        icon=INPUT + "/GamepadSwitch/T_UI_Controller-Switch.T_UI_Controller-Switch",
        inputmap=INPUTMAP + "/SwitchScreens/W_InputMapSwitchProController.W_InputMapSwitchProController_C",
        label="Nintendo Switch", tested=False),
}

# The controller pictures are not chosen through CommonUI at all. The packed
# UI config names one per platform, and every PC platform gets the Xbox pad.
# Rather than repaint those textures, this points the config at the art the
# game already has for the real controller. A mod container replaces the file
# instead of merging into it, so the whole thing ships, edited in place.
UICONFIG = "Dungeons/Config/DefaultUIConfig.ini"
XSX_ICON = INPUT + "/GamepadXboxSeriesX/T_UI_Controller-XSX.T_UI_Controller-XSX"
XBOX_INPUTMAP = INPUTMAP + "/XboxScreens/W_InputMapXbox.W_InputMapXbox_C"
# PC.Steam is Steam and PC.Launcher is presumably the Microsoft Store build.
# Xbox and Unknown are moved too, since this only ever runs on a PC.
XSX_PLATFORMS = ["SW.Platform.PC.Launcher", "SW.Platform.Unknown",
                 "SW.Platform.Xbox", "SW.Platform.PC.Steam"]

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


def read_uiconfig(paks, key):
    """Pull DefaultUIConfig.ini out of the game's legacy pak into work/."""
    cached = os.path.join(WORK, "DefaultUIConfig.ini")
    if not os.path.exists(cached):
        os.makedirs(WORK, exist_ok=True)
        out = subprocess.run([tool("repak"), "-a", key, "get",
                              os.path.join(paks, "Dungeons-Windows.pak"), UICONFIG],
                             check=True, stdout=subprocess.PIPE).stdout
        if not out:
            die("read nothing for %s, is the key right?" % UICONFIG)
        open(cached, "wb").write(out)
    return open(cached, "rb").read()


def edit_uiconfig(raw, tag):
    """Point the controller picture and the controls screen at the variant's
    controller. Every line touched is checked against what the game ships, so
    a patch that reshuffles the config stops the build instead of producing a
    mod that edits nothing."""
    v = VARIANTS[tag]
    text = raw.decode("utf-8-sig")
    swaps = [('((TagName="%s"), "%s")' % (p, XSX_ICON),
              '((TagName="%s"), "%s")' % (p, v["icon"])) for p in XSX_PLATFORMS]
    swaps.append(('(TagName="SW.UI.WidgetName.InputMap.Xbox"),LayerName=(TagName="SW.UI.Slot.System"),'
                  'StateChildUserWidget="%s"' % XBOX_INPUTMAP,
                  '(TagName="SW.UI.WidgetName.InputMap.Xbox"),LayerName=(TagName="SW.UI.Slot.System"),'
                  'StateChildUserWidget="%s"' % v["inputmap"]))
    for old, new in swaps:
        n = text.count(old)
        if n != 1:
            die("expected %s once in %s, found it %d times; the game's config has"
                " changed shape" % (old, UICONFIG, n))
        text = text.replace(old, new)
    print("  %-12s controller picture -> %s, controls screen -> %s"
          % (tag, v["icon"].rsplit(".", 1)[-1], v["inputmap"].rsplit("/", 1)[-1].split(".")[0]))
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return bom + text.encode("utf-8")


def package(tag, staged, key, version, uiconfig):
    out = os.path.join(DIST, tag)
    os.makedirs(out, exist_ok=True)
    subprocess.run([tool("retoc"), "-a", key, "to-zen", "--version", "UE5_6",
                    staged, os.path.join(out, "Dungeons-Windows_P.utoc")],
                   check=True, stdout=subprocess.DEVNULL)

    # retoc leaves an empty stub .pak next to the pair. Overwrite it with one
    # holding the edited config; that is the route mcd2-skip-splash proved.
    loose = os.path.join(WORK, "loose", tag)
    shutil.rmtree(loose, ignore_errors=True)
    cfg = os.path.join(loose, *UICONFIG.split("/"))
    os.makedirs(os.path.dirname(cfg))
    open(cfg, "wb").write(edit_uiconfig(uiconfig, tag))
    pak = os.path.join(out, "Dungeons-Windows_P.pak")
    subprocess.run([tool("repak"), "pack", "--mount-point", "../../../", loose, pak],
                   check=True, stdout=subprocess.DEVNULL)
    listed = subprocess.run([tool("repak"), "list", pak], check=True,
                            stdout=subprocess.PIPE, text=True).stdout.split()
    if listed != [UICONFIG]:
        die("the pak holds %s, expected only %s" % (listed, UICONFIG))

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
    keyfile = os.path.join(TOOLS, "aes_key.txt")
    if not key and os.path.exists(keyfile):
        key = open(keyfile).read().strip()
    if not key:
        die("set MCD2_AES_KEY to the game's container key, or put it in"
            " tools/aes_key.txt (see docs/building.md)")

    meta = json.load(open(os.path.join(HERE, "nexus", "variants.json"), encoding="utf-8"))
    version = meta.get("version", "1.0")

    wanted = sys.argv[1:] or list(VARIANTS)
    for t in wanted:
        if t not in VARIANTS:
            die("unknown variant %r, expected one of %s" % (t, ", ".join(VARIANTS)))

    paks = game_paks()
    print("reading assets from %s" % paks)
    assets = extract(paks, key)
    uiconfig = read_uiconfig(paks, key)
    print("building:")
    for t in wanted:
        package(t, build(t, assets), key, version, uiconfig)
    print("\ndone, packages are in dist/")


if __name__ == "__main__":
    main()
