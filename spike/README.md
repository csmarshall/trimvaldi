# spike/ — throwaway feasibility proof

**This is not the theme. It is expected to be deleted.** It exists to answer four
questions before any time goes into polish. Run against Vivaldi **8.1.4087.55**
(arm64 macOS) on 2026-07-21.

```sh
./spike/setup.sh                  # fresh profile -> themed, verified chrome
python3 spike/theme-patch.py .dev-profile   # (Vivaldi must be closed)
./spike/setup.sh --stop
```

## Headline: a real install needs ZERO manual GUI steps

Measured, not estimated. `setup.sh` goes from an empty directory to rendered,
verified custom chrome with no clicking, and two negative controls confirm it is
our writes doing it rather than a default.

Everything below is a **pref write while Vivaldi is closed** — the whole recipe:

| What | Pref | Value |
|---|---|---|
| Register the CSS folder | `vivaldi.appearance.css_ui_mods_directory` | path (string) |
| Vertical tab bar | `vivaldi.tabs.bar.position` | **`1`** (int — see below) |
| Palette, accent, radius | `vivaldi.themes.user` + `.current` | theme objects |
| Light/dark mapping | `vivaldi.theme.schedule.o_s` | `{light, dark}` ids |

## The four findings that actually matter

### 1. Enum prefs are stored as INTEGERS — this was the Q7 "blocker"

`Resources/vivaldi/prefs_definitions.json` is an **authoritative registry of 618
prefs with types and defaults**. It says:

    vivaldi.tabs.bar.position => {"type":"enum",
                                  "enum_values":{"top":0,"left":1,"right":2,"bottom":3}}

The previous attempt wrote the **string** `"left"`. The JSON store accepted it —
hence "stored but ignored" — and the enum reader discarded it as malformed and fell
back to `top`. Writing `1` works immediately.

**Consequence:** check `prefs_definitions.json` for a pref's *type* before writing it.
That file supersedes grepping the JS bundle for pref names, and it is the natural
input to ADR-0004's levelset tests.

### 2. The CSS-mods endpoint emits `@import`, alphabetically

`chrome://vivaldi-data/css-mods/css` is **not** a concatenation:

    @import url("00-alpha.css");
    @import url("99-omega.css");

So load order **is** controllable by filename, and `@import` resolves. This settles
the open question in `css/README.md` and leaves ADR-0006 intact. Note that imported
sheets are **not** in `document.styleSheets` — recurse via `rule.styleSheet` when
introspecting, or you will conclude your own rules are missing.

The `vivaldi-css-mods` experiment flag is **not required** on this build, and
`vivaldi.features.css_mods` (which vivaldi-peek documents) **does not exist**
anywhere in it. Do not copy that recipe verbatim.

### 3. Source order breaks ties; it does not beat Vivaldi

    #tabs-tabbar-container { background: #c00 }                     → SILENTLY LOST
    #browser:not(.transparent-tabbar) #tabs-tabbar-container { … }  → Vivaldi's, (2,1,0)

ADR-0006's "later wins" holds for **our own token layering** (user overrides vs our
defaults — equal-specificity blocks). It does **not** mean our rules beat Vivaldi's.
Every structural rule must match or exceed Vivaldi's specificity, and when it fails
it fails **invisibly**. This is exactly the failure mode ADR-0002 predicted.

### 4. The theme engine writes 117 variables INLINE — so define a theme, don't fight one

Vivaldi computes its palette in JS and writes ~117 `--color*` properties as a
**5,306-character inline `style` attribute on `#browser`**. Inline beats all author
CSS, so recolouring from a stylesheet would need `!important` on every variable.

But those 117 are **derived** from a theme object of about **five seed colours**. So
the palette ports as a native theme (`spike/theme-patch.py`), which is less code,
survives selector churn, and is still fully scriptable. It also gets us
`accentFromPage: false` — killing `.color-accent-from-page`, the single
highest-value setting for zero-blue — and `backgroundImage: ""` for flat chrome.

**Verified: the engine preserves hue.** Every derived variable came back exactly
neutral (R=G=B) from our neutral seeds, so zero-blue survives derivation.

## What did NOT work cleanly

- **`!important` is unavoidable for the strip width.** Vivaldi writes
  `style="width: 360px"` inline on `#tabs-tabbar-container` from
  `vivaldi.tabs.bar.width`. No selector avoids an inline style. It does not break the
  override contract — the `!important` rule's *value* is still a token, so
  `--tf-strip-collapsed` in `user-overrides.css` still wins — but ADR-0006 should say
  so explicitly rather than let it be discovered later.
- **The derived ramp clipped at trimfox's base — FIXED by lifting the seed.** With
  `colorBg: #202020`, `--colorBgIntenser` derived to `#000000` and `--colorBgIntense`
  to `#0c0c0c`, because Vivaldi's derivation assumes roughly its own base's headroom
  (`#363536` = 54/255). Lifting the seed to **`#2a2a2a`** (42/255) resolves it while
  staying exactly neutral. Measured after the change, dark:

      BgIntenser #0f0f0f · BgIntense #181818 · BgDarker #1f1f1f · BgDark #242424
      Bg #2a2a2a · BgLight #2e2e2e · BgLightIntense #323232 · BgLighter #3e3e3e

  and light (`#ececec` seed, unchanged): `#dddddd → #ffffff`. **All rungs neutral in
  both.** We deliberately did *not* adopt Vivaldi's own base, which is non-neutral
  (`#363536`, plus `colorFg #d3d9e3`) — we took its luminance, never its cast.
  **Knock-on to check when styling:** `--tf-surface` and `--tf-raised` are now only 4
  apart (`#2a2a2a`/`#2e2e2e`) where trimfox had 14, so hover states may read weakly.
- **At rest the tab-count separator lines read too faintly** to convey shape. Needs
  real design work; the mechanism is there.
- **Untested:** update survival (Q6) is still inherited reasoning, not measured. Also
  untested: how the theme behaves if the user edits themes in Vivaldi's own Settings
  UI afterwards, and whether `engineVersion: 1` stays valid across releases.

## Files

    setup.sh          scripted, zero-GUI-step install + launch + verify
    theme-patch.py    installs the grayscale palette as a native Vivaldi theme
    css/00-alpha.css  load-order probe
    css/10-palette.css  trimfox grayscale, --tf-* tokens, .theme-dark/.theme-light
    css/20-map.css    --tf-* → --color* map. SUPERSEDED IN PRACTICE by theme-patch.py;
                      kept to document why the CSS route loses to inline styles.
    css/30-strip.css  collapsed hover-expand rail (the signature)
    css/99-omega.css  load-order probe
