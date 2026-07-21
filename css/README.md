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

**Unresolved:** how Vivaldi actually loads a folder of CSS, and therefore whether
load order is controllable by filename or needs a single entry file with `@import`.
That is Q1 in [`../docs/vivaldi-research.md`](../docs/vivaldi-research.md) and must
be answered before this structure is locked in.
