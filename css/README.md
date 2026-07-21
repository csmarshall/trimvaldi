# css/

The Vivaldi custom-UI stylesheets — the theme itself. **Empty so far.**

Planned shape, mirroring trimfox's layering so the override contract feels the same:

    dials.css              structural / motion / type defaults (--tf-* knobs)
    palettes/
      grayscale.css        default: zero-blue, all gray
      tinted.css           parametric one-hue palette via oklch()
    trimvaldi.css          the theme rules themselves
    user-overrides.css     personal, gitignored, loaded LAST so it wins by
                           source order — no !important needed

Load order is the whole contract: dials → palette → theme → user overrides. A user
redefining a token in `user-overrides.css` gets exactly the behaviour of having
changed the default, and `git pull` never conflicts with their colours.

**✅ RESOLVED 2026-07-21** (was: "how does Vivaldi load a folder of CSS?").

`chrome://vivaldi-data/css-mods/css` generates one `@import` per `.css` in the folder,
**in alphabetical order**. So load order is controllable **both** ways — numeric
filename prefixes *or* a single entry file that `@import`s the rest. `@import` does
resolve from that endpoint. See [`../docs/vivaldi-research.md`](../docs/vivaldi-research.md)
Q1 and [`../docs/adr/0006-import-order-not-cascade-layers.md`](../docs/adr/0006-import-order-not-cascade-layers.md).

The structure above can be locked in. Two amendments the spike forced:

- **The palette is NOT a stylesheet.** Vivaldi's theme engine writes ~117 `--color*`
  properties as an inline `style` on `#browser`, so CSS cannot override them without
  `!important` on every one. Instead the palette installs as a **native Vivaldi theme**
  via prefs, derived from ~5 seed colours. `palettes/*.css` becomes the `--tf-*` token
  definitions plus a generator input for that theme — not the recolouring mechanism.
- **Prefix files numerically** (`00-`, `10-`, …) so alphabetical order *is* the
  intended cascade order, and `user-overrides.css` sorts last on its own.
