# trimvaldi

A Vivaldi UI theme carrying over the design language of
[trimfox](https://github.com/csmarshall/trimfox) — grayscale, zero-blue, and
trimmed down to the tabs.

> **Status: feasibility proven, theme not built.** There is still nothing to install.
> What exists is a throwaway proof that the approach works, plus the research and
> decisions behind it. Public early so the work is legible, not because it is usable.

What the feasibility spike established against Vivaldi 8.1.4087.55 on macOS:

- **Setup needs zero manual steps in Settings.** Registering the CSS folder, the
  vertical tab strip, and the whole palette are all pref writes to a closed profile.
  Measured end to end, with controls — not estimated.
- **The signature interaction works** — a collapsed tab rail that expands on hover
  and *overlays* the page rather than reflowing it.
- **The palette is a Vivaldi theme, not a stylesheet.** Vivaldi derives ~117 chrome
  variables from about five seed colours, so trimfox's grayscale ports as a native
  theme. Its light/dark values carried over unchanged.

Honest limits, since they matter more than the wins:

- **Whether UI mods survive a Vivaldi update is unverified.** Mods live in the user
  profile rather than the app bundle, which suggests they should, but we have not
  observed an actual update against a modded profile. Treat it as untested.
- A little `!important` is unavoidable, because Vivaldi sets some values as inline
  styles. It does not affect your ability to override — see below.
- Everything above was measured against **one build on one platform**.

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
  (`oklch()` is confirmed working in Vivaldi's UI layer)
- The trim pass — strip the chrome to the trimfox silhouette
- Hover-expand tab strip styling on Vivaldi's native vertical tabs
- A `user-overrides.css` layer so you can customize without forking
- A scripted installer, so setup stays a single command

You will still customize by redefining `--tf-*` tokens in your own
`user-overrides.css`, exactly as in trimfox, and you will never need `!important`
to override trimvaldi or need to run any build step to do it.

See [`docs/migration-brief.md`](docs/migration-brief.md) for the plan,
[`docs/adr/`](docs/adr/) for the decisions and why, and
[`docs/vivaldi-research.md`](docs/vivaldi-research.md) for what is verified versus
still open — the distinction is marked per item, deliberately.

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
