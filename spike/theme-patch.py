#!/usr/bin/env python3
"""SPIKE — throwaway. Install the trimfox grayscale palette as a native Vivaldi THEME.

The discovery this rests on: Vivaldi's theme engine writes all ~117 --color*
custom properties as a single 5KB INLINE style attribute on #browser. CSS can
only beat an inline style with !important, so overriding the palette from a
stylesheet means !important on every mapped variable.

But those 117 variables are DERIVED, by the engine, from a theme object of only
about five seed colours. Defining a theme is therefore both far less code and
genuinely "with the grain" — it drives the engine rather than fighting its output.

Themes live in the `vivaldi.themes.user` pref (a list), selected by
`vivaldi.themes.current`, with light/dark mapped by `vivaldi.theme.schedule.o_s`.
All three are ordinary prefs, so this stays fully scriptable: still zero GUI steps.

Usage:  theme-patch.py <profile-dir>          (Vivaldi MUST be closed)
"""
import json
import pathlib
import sys

# The trimfox grayscale palette, seed colours only.
# Source: ~/work/trimfox/chrome/palettes/grayscale.css — values verbatim.
PALETTES = {
    "dark": {
        # DELIBERATE DEVIATION from trimfox, which uses #202020 for --tf-surface.
        # Vivaldi derives its whole dark ramp by offsetting DOWN from colorBg, and
        # assumes roughly Vivaldi2's headroom (#363536 = 54/255). At 32/255 the
        # bottom rung clipped to pure #000000 and --colorBgIntense collapsed to
        # #0c0c0c. Lifting to 42/255 restores the headroom while staying exactly
        # neutral — Vivaldi's own base is NOT neutral (#363536, and colorFg
        # #d3d9e3 is openly blue), so we take its luminance, never its cast.
        # ADR-0001: ethos wins, implementation changes.
        "colorBg":          "#2a2a2a",   # --tf-surface, lifted from trimfox's #202020
        "colorFg":          "#ffffff",   # --tf-text
        "colorAccentBg":    "#707070",   # --tf-accent
        "colorHighlightBg": "#555555",   # --tf-select  (replaces Vivaldi's #7aa0ff)
        "colorWindowBg":    "#1c1c1c",   # --tf-content
    },
    "light": {
        "colorBg":          "#ececec",
        "colorFg":          "#111111",
        "colorAccentBg":    "#707070",
        "colorHighlightBg": "#b8b8b8",
        "colorWindowBg":    "#f7f7f7",
    },
}

# Structural knobs, identical for both. These encode ethos decisions:
#   accentFromPage  — Vivaldi tints chrome from the page's theme colour. Directly
#                     hostile to zero-blue grayscale. THE highest-value single
#                     setting for the look.
#   backgroundImage — Vivaldi paints bg_dark-8.png behind the chrome. Flat only.
#   blur / alpha    — no translucency; trimfox chrome is opaque.
#   radius          — Vivaldi defaults to 8px, much rounder than trimfox.
STRUCTURE = {
    "engineVersion": 1,
    "version": 1,
    "accentFromPage": False,
    "accentOnWindow": False,
    "accentSaturationLimit": 0,
    "preferSystemAccent": False,
    "alpha": 1,
    "blur": 0,
    "contrast": 0,
    "radius": 3,
    "backgroundImage": "",
    "backgroundPosition": "stretch",
    "backgroundSource": "",
    "colorPosition": "unified",
    "transparencyTabBar": False,
    "transparencyTabs": False,
    "url": "",
}


def theme(variant):
    return {
        **STRUCTURE,
        **PALETTES[variant],
        "id": f"trimvaldi-{variant}",
        "name": f"trimvaldi {variant}",
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    prefs = pathlib.Path(sys.argv[1]) / "Default" / "Preferences"

    try:
        data = json.loads(prefs.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    themes = [theme("dark"), theme("light")]
    ours = {t["id"] for t in themes}

    viv = data.setdefault("vivaldi", {})
    user = viv.setdefault("themes", {}).setdefault("user", [])
    # Idempotent: drop any previous trimvaldi entries before re-adding.
    user[:] = [t for t in user if t.get("id") not in ours] + themes

    viv["themes"]["current"] = "trimvaldi-dark"
    # Follow the OS appearance, but with our two themes on each side of the switch.
    viv.setdefault("theme", {}).setdefault("schedule", {})["o_s"] = {
        "light": "trimvaldi-light",
        "dark": "trimvaldi-dark",
    }

    prefs.parent.mkdir(parents=True, exist_ok=True)
    prefs.write_text(json.dumps(data, indent=2))
    print(f"  installed themes {sorted(ours)} into {prefs}")


if __name__ == "__main__":
    main()
