# trimvaldi

A Vivaldi UI theme carrying over the design language of
[trimfox](https://github.com/csmarshall/trimfox) — grayscale, zero-blue, and
trimmed down to the tabs.

> **Status: pre-implementation.** Nothing is built yet. This repo currently holds
> the migration brief and a research log. It is public early so the work is legible,
> not because it is usable — there is no theme to install.

## What this will be

trimfox's premise is *trim everything that isn't a tab*: a skinny tab strip that
expands on hover, no favicons or pills or close buttons in the collapsed state, a
small consistent chrome typeface, and a palette with every stock accent neutralized
to gray — with one-hue tinting available through `oklch()` if you want colour back.

trimvaldi aims to bring that to Vivaldi.

## Why it is a rewrite, not a port

Vivaldi has no `userChrome.css`. Firefox chrome is XUL styled through that file;
Vivaldi is Chromium-based and its UI is an ordinary web app styled with ordinary
CSS against ordinary DOM. Both are "CSS" and that is where it ends — **no shared
selectors, no shared variables, no shared install mechanics.**

So trimvaldi inherits trimfox's *design language* and *token architecture*
(`--tf-*` dials, swappable palettes, a user-override layer that wins by source
order rather than `!important`) and inherits none of its rules.

One happy consequence: Vivaldi already ships native vertical tabs and tab stacking,
so much of what trimfox had to build by hand comes free here. The work becomes the
trimming and the palette rather than the tab strip itself.

## Planned

- Grayscale-by-default palette, with the parametric OKLCH tinting from trimfox
- The trim pass — strip the chrome to the trimfox silhouette
- Hover-expand tab strip styling on Vivaldi's native vertical tabs
- A `user-overrides.css` layer so you can customize without forking

See [`docs/migration-brief.md`](docs/migration-brief.md) for the full plan and
[`docs/vivaldi-research.md`](docs/vivaldi-research.md) for what still needs
verifying against a real Vivaldi install.

## Related

- [trimfox](https://github.com/csmarshall/trimfox) — the Firefox original
- [trimfox-drift](https://github.com/csmarshall/trimfox-drift) — companion tool that
  watches for Firefox chrome drift

## How this is being built

Hand-directed and AI-assisted: every decision reviewed, understood, and driven by a
human, with AI used as a power tool for scaffolding, docs, and research. Provenance
is disclosed honestly per artifact rather than claimed wholesale in either
direction.

## License

MIT © 2026 Charles Marshall
