#!/usr/bin/env python3
"""Apply trimvaldi's settings recipe to a Vivaldi profile.

This is [ADR-0004]'s "scripted Preferences patch gated by levelset tests", and it
supersedes the throwaway spike/setup.sh + spike/theme-patch.py.

A large share of trimvaldi is a PREF, not CSS ([ADR-0007]): the palette, the vertical
tab strip, and much of the trim. This tool is therefore roughly half the theme.

THE LEVELSET (ADR-0004), which is the point of the whole design:

  Every pref written here is validated against Vivaldi's OWN registry —
  Resources/vivaldi/prefs_definitions.json, 618 prefs with types and defaults —
  BEFORE anything is written. If Vivaldi renames a pref, changes its type, or drops
  an enum value, this refuses to run instead of silently writing something the
  browser will ignore.

  Enum values are declared BY LABEL below ("left", "off") and converted to their
  integer here. That is deliberate and structural: enum prefs are stored as INTEGERS,
  and writing the string label persists silently and is then ignored — a failure that
  looks exactly like a hard blocker and cost a full session to diagnose. Declaring
  labels and converting from the registry makes that bug unrepresentable.

⚠️ Vivaldi MUST be closed. It owns Preferences and rewrites it on exit, silently
   clobbering edits. This tool refuses to run while Vivaldi is up.

Usage:
    ./tools/apply-settings.py <profile-dir> [--css-dir DIR] [--dry-run]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
VIVALDI_FRAMEWORKS = pathlib.Path(
    "/Applications/Vivaldi.app/Contents/Frameworks/Vivaldi Framework.framework/Versions")


# ── The recipe ──────────────────────────────────────────────────────────────────
# Each entry is (pref path, value). Enum values are LABELS, converted below.
# `DictMerge` patches only the named keys of a dictionary pref, leaving the rest.
class DictMerge(dict):
    """Marker: merge these keys into the existing dict rather than replacing it."""


def recipe(css_dir):
    return [
        # Register our stylesheets. The ONLY load-bearing pref for CSS mods — the
        # `vivaldi-css-mods` experiment flag is not required (research Q1).
        ("vivaldi.appearance.css_ui_mods_directory", str(css_dir)),

        # The signature: vertical tab strip. Enum — declared as a label on purpose.
        ("vivaldi.tabs.bar.position", "left"),

        # ── Trim ────────────────────────────────────────────────────────────────
        # Status bar. trimfox has no equivalent; Vivaldi adds one. Enum label.
        ("vivaldi.status_bar.display", "off"),

        # Panel rail. Charles's test: everything it exposes is reachable by keyboard
        # shortcut or menu, so a permanently-visible icon column is not earning its
        # space. `barVisible` is separate from `panelVisible`, so this removes the
        # AFFORDANCE and keeps the CAPABILITY — panels still open on demand.
        # NOTE: both keys must be set. `state` is the current window;
        # `window_defaults` is what NEW windows inherit. Setting only the first
        # means the rail reappears on the next new window.
        ("vivaldi.panels.state", DictMerge(barVisible=False)),
        ("vivaldi.panels.window_defaults", DictMerge(barVisible=False)),

        # Panels overlay content instead of pushing it when they do open — natively
        # the behaviour ADR-0005 argues for on the tab strip.
        ("vivaldi.panels.as_overlay.enabled", True),
    ]


# ── The palette, as a native Vivaldi theme (ADR-0007) ───────────────────────────
# Seeds only; Vivaldi derives ~117 --color* properties from these.
# TODO(ADR-0008): generate this and css/ from ONE palette definition. Until then
# these values are the source of truth and css/00-selectors.css aliases them.
PALETTES = {
    # trimfox's grayscale ramp, lifted uniformly by +10 so Vivaldi's derivation has
    # the headroom it assumes. trimfox's GAPS are preserved exactly (10/4/14/39);
    # its absolute values are not the design.
    "dark":  {"colorBg": "#2a2a2a", "colorFg": "#ffffff", "colorAccentBg": "#707070",
              "colorHighlightBg": "#5f5f5f", "colorWindowBg": "#262626"},
    "light": {"colorBg": "#ececec", "colorFg": "#111111", "colorAccentBg": "#707070",
              "colorHighlightBg": "#b8b8b8", "colorWindowBg": "#f7f7f7"},
}

STRUCTURE = {
    "engineVersion": 1, "version": 1,
    # THE highest-value single setting for zero-blue: Vivaldi tints its chrome from
    # the page's theme colour by default, which is directly hostile to a grayscale
    # palette.
    "accentFromPage": False,
    "accentOnWindow": False, "accentSaturationLimit": 0, "preferSystemAccent": False,
    "alpha": 1, "blur": 0, "contrast": 0, "radius": 3,
    "backgroundImage": "", "backgroundPosition": "stretch", "backgroundSource": "",
    "colorPosition": "unified", "transparencyTabBar": False,
    "transparencyTabs": False, "url": "",
}


def themes():
    return [{**STRUCTURE, **PALETTES[v], "id": f"trimvaldi-{v}",
             "name": f"trimvaldi {v}"} for v in ("dark", "light")]


# ── Vivaldi's pref registry ─────────────────────────────────────────────────────
def load_registry():
    versions = sorted(p for p in VIVALDI_FRAMEWORKS.iterdir() if p.name[0].isdigit()) \
        if VIVALDI_FRAMEWORKS.is_dir() else []
    if not versions:
        sys.exit("2: Vivaldi not found — is it installed?")
    path = versions[-1] / "Resources" / "vivaldi" / "prefs_definitions.json"
    if not path.exists():
        sys.exit(f"2: pref registry missing at {path}")

    def walk(node, trail):
        if isinstance(node, dict):
            if "type" in node and "default" in node:
                yield ".".join(trail), node
                return
            for k, v in node.items():
                yield from walk(v, trail + [k])

    return dict(walk(json.loads(path.read_text()), [])), versions[-1].name


def levelset(entries, registry):
    """Validate the whole recipe BEFORE writing anything. Returns resolved values."""
    resolved, problems = [], []
    for path, value in entries:
        spec = registry.get(path)
        if spec is None:
            problems.append(f"{path}: NOT in Vivaldi's pref registry (renamed? removed?)")
            continue
        kind = spec["type"]

        if kind == "enum":
            values = spec.get("enum_values", {})
            if value not in values:
                problems.append(
                    f"{path}: {value!r} is not a valid enum label; "
                    f"registry offers {sorted(values)}")
                continue
            resolved.append((path, values[value], f"enum {value!r} -> {values[value]}"))
        elif kind in ("string", "file_path"):
            if not isinstance(value, str):
                problems.append(f"{path}: expected string, got {type(value).__name__}")
                continue
            resolved.append((path, value, kind))
        elif kind == "boolean":
            if not isinstance(value, bool):
                problems.append(f"{path}: expected boolean, got {type(value).__name__}")
                continue
            resolved.append((path, value, kind))
        elif kind == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                problems.append(f"{path}: expected integer, got {type(value).__name__}")
                continue
            resolved.append((path, value, kind))
        elif kind == "dictionary":
            if not isinstance(value, dict):
                problems.append(f"{path}: expected dictionary, got {type(value).__name__}")
                continue
            unknown = set(value) - set(spec.get("default", {}))
            if unknown:
                problems.append(f"{path}: keys not in the registry default: {sorted(unknown)}")
                continue
            resolved.append((path, value, "dictionary (merge)"))
        elif kind == "list":
            if not isinstance(value, list):
                problems.append(f"{path}: expected list, got {type(value).__name__}")
                continue
            resolved.append((path, value, kind))
        else:
            problems.append(f"{path}: unhandled registry type {kind!r}")
    return resolved, problems


def set_path(data, path, value):
    node = data
    parts = path.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    if isinstance(value, DictMerge):
        node.setdefault(parts[-1], {}).update(value)
    else:
        node[parts[-1]] = value


def vivaldi_running():
    return subprocess.run(["pgrep", "-f", "MacOS/Vivaldi"],
                          capture_output=True).returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", type=pathlib.Path)
    ap.add_argument("--css-dir", type=pathlib.Path, default=REPO / "css")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if vivaldi_running():
        sys.exit("2: Vivaldi is RUNNING. It rewrites Preferences on exit and would "
                 "clobber these edits. Quit it first.")

    registry, version = load_registry()
    print(f"Vivaldi {version} — {len(registry)} prefs in registry\n")

    entries = recipe(args.css_dir.resolve())
    resolved, problems = levelset(entries, registry)

    for path, value, how in resolved:
        print(f"  ok    {path}\n          = {json.dumps(value)}   [{how}]")
    for p in problems:
        print(f"  FAIL  {p}")
    if problems:
        sys.exit("\n1: levelset failed — NOTHING was written. Vivaldi's pref surface "
                 "has changed; reconcile the recipe against prefs_definitions.json.")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return

    prefs_file = args.profile / "Default" / "Preferences"
    try:
        data = json.loads(prefs_file.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    for path, value, _ in resolved:
        set_path(data, path, value)

    # Themes (ADR-0007). Idempotent: drop previous trimvaldi entries before adding.
    ours = themes()
    ids = {t["id"] for t in ours}
    user = data.setdefault("vivaldi", {}).setdefault("themes", {}).setdefault("user", [])
    user[:] = [t for t in user if t.get("id") not in ids] + ours
    data["vivaldi"]["themes"]["current"] = "trimvaldi-dark"
    # `schedule.enabled` defaults to `system`, and while it is, the OS appearance
    # OVERRIDES themes.current — so the o_s map must be set too or the active theme
    # silently is not the one selected.
    data["vivaldi"].setdefault("theme", {}).setdefault("schedule", {})["o_s"] = {
        "light": "trimvaldi-light", "dark": "trimvaldi-dark"}
    print(f"  ok    vivaldi.themes.user\n          = {sorted(ids)}   [ADR-0007]")

    prefs_file.parent.mkdir(parents=True, exist_ok=True)
    prefs_file.write_text(json.dumps(data, indent=2))
    print(f"\nWrote {prefs_file}")


if __name__ == "__main__":
    main()
