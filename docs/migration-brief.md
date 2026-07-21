# Migration brief — trimfox (Firefox) → trimvaldi (Vivaldi)

The standing brief for this project. Read with `../CLAUDE.md`.

## The ask

Charles wants the trimfox look and feel — his macOS Firefox `userChrome` theme —
reproduced as a Vivaldi theme.

**Source of truth for the design:** `~/work/trimfox`
(GitHub: `csmarshall/trimfox`; live palette picker:
https://csmarshall.github.io/trimfox/tint-picker.html)

Read that repo for intent, not for code. Especially:

| Path in `~/work/trimfox` | Why it matters here |
|---|---|
| `README.md` | The pitch and the look, in Charles's words |
| `chrome/dials.css` | The full knob surface — structure, motion, font scale |
| `chrome/palettes/` | `grayscale.css` (default), `firefox.css`, `tinted.css` (OKLCH) |
| `docs/customizing.md` | How the override layer is meant to feel to a user |
| `docs/adr/` | Why each decision was made — the reasoning we want to preserve |
| `docs/screenshots/` | What "done" looks like |

## What ports, and what does not

**Ports (the design language):**

- Grayscale by default, zero-blue. Every stock accent neutralized.
- Extreme trim: no favicons in the collapsed strip, no pills, no close buttons,
  no new-tab button, no hover-preview cards, no launcher clutter.
- Skinny tab strip that expands on hover to readable labels.
- Small chrome type driven by one font-size token with a computed scale.
- One-hue tinting: the whole palette derived from `--tf-hue` + `--tf-chroma`
  through `oklch()`. Chromium supports `oklch()`, so this maths carries over
  essentially intact — this is the single biggest genuine reuse available.
- Token architecture: dial defaults → palette → user overrides, resolved by
  source order, no `!important`.

**Does not port (anything mechanical):**

- Every selector. Firefox XUL ids/classes (`#urlbar`, `.tabbrowser-tab`,
  `.urlbarView-row`, `#nav-bar`, …) do not exist in Vivaldi.
- Firefox chrome variables (`--toolbar-bgcolor`, `--button-color`, …).
- `user.js` / prefs, `autoconfig`, `install.sh` — different install mechanics
  entirely (see `vivaldi-research.md`).
- `refined-findbar/`, the XUL menu work, native-context-menu prefs — all
  Firefox-specific problems that simply do not exist in Vivaldi.
- `trimfox-drift`. It parses Firefox's chrome for private-API drift. A Vivaldi
  equivalent would be a separate build against Vivaldi's DOM — worth considering
  eventually, but out of scope until there is a theme to monitor.

## Token surface to carry over

Keep the `--tf-*` names identical to trimfox so a palette reads the same in both
repos and the two themes stay legibly one family.

Colour tokens (from `chrome/palettes/`):

    --tf-surface  --tf-raised   --tf-field    --tf-content
    --tf-text     --tf-text-dim --tf-glyph
    --tf-line     --tf-line-inactive  --tf-line-solid  --tf-line-solid-inactive
    --tf-accent   --tf-accent-hover   --tf-accent-active
    --tf-select   --tf-highlight      --tf-highlight-inactive
    --tf-attention
    --tf-hue      --tf-chroma          (drive the parametric OKLCH palette)

Structure / motion / type tokens (from `chrome/dials.css`):

    --tf-sep-inset  --tf-anim
    --tf-font-family  --tf-font-size  --tf-fs-lift
    --tf-fs-xs/-sm/-md/-field/-lg/-h/-xl/-xxl

Note `--tf-font-family: -apple-system` — same on Chromium/macOS, so it carries.
Keep the reduced-motion guard that forces `--tf-anim: 0s`; it is an accessibility
floor, not a preference.

## Proposed phases

Nothing here is committed to; it is a starting shape to react to.

0. **Install Vivaldi** and enable custom UI CSS. Blocked on this — see
   `vivaldi-research.md`. Until done, everything below is theory.
1. **Recon.** Open Vivaldi's UI in its own devtools, map the real DOM: tab bar,
   address bar, panels, menus. Record actual selectors in `vivaldi-research.md`.
   This is the step that replaces "read Firefox's chrome CSS."
2. **Palette first.** Port `grayscale.css` and the OKLCH `tinted.css` onto
   Vivaldi's theme variables. Vivaldi has its own theme engine with a colour UI —
   decide whether to drive it or bypass it (open decision below).
3. **Trim pass.** Hide the clutter; get the chrome down to the trimfox silhouette.
4. **Tab strip.** Vivaldi's vertical tabs are native, so this is styling and
   hover-expand behaviour, not construction.
5. **Override layer.** Reproduce the `user-overrides.css`-loads-last contract so
   users customize without forking.
6. **Docs + install.** README, screenshots matching trimfox's set, install steps.

## Open decisions

- **Vivaldi theme engine: drive it or bypass it?** Vivaldi ships a real theming UI
  with its own colour variables. Mapping `--tf-*` onto those would make trimvaldi
  cooperate with Vivaldi's light/dark switching and any user theme — but constrains
  us to its model. Bypassing gives full control and closer trimfox fidelity, at the
  cost of fighting the app. Decide during phase 2, with the DOM in front of us.
- **Scope of parity.** Is trimvaldi meant to be pixel-faithful to trimfox, or
  "trimfox's philosophy applied natively to Vivaldi"? These diverge fast, because
  Vivaldi's UI affordances differ. Charles's call.
- **Name.** "trimvaldi" is the working name and may not survive.
