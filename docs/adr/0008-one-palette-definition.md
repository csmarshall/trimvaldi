# ADR-0008 — One palette definition generates both outputs

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0005 — `--tf-*` token API and swappable palettes](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0005-token-api.md)
- **Follows from:** [ADR-0007](0007-palette-is-a-native-theme.md)

## Context

[ADR-0007](0007-palette-is-a-native-theme.md) splits the palette across two
representations that must agree:

| Representation | Consumer |
|---|---|
| ~5 **theme seed colours** in a prefs JSON object | Vivaldi's theme engine — recolours the chrome |
| The full **`--tf-*` token set** in CSS | *Our own* rules — the strip, trim, structure |

In the spike these were two hand-edited files kept in sync by hand. That is exactly
the silent-drift hazard [ADR-0002](0002-centralize-selectors.md) was written about,
and it is a hazard **trimfox never faced**, because trimfox's palette was CSS and
nothing else.

It is also unusually hard to notice. A disagreement does not error and does not look
broken — the chrome renders in one set of grays and our own rules render in another,
slightly different set. The result reads as "the theme is a bit off" rather than as a
bug with a location.

The spike already demonstrated how fine-grained the coupling is. `--tf-line-solid` is
not a chosen colour at all; it is *derived* — the opaque form of `--tf-line`
composited over `--tf-surface`, so that a tab separator reads identically over the
active-tab highlight and over a dark inactive tab:

    line-solid = surface + alpha × (255 − surface)

Lifting `--tf-surface` therefore silently invalidates `--tf-line-solid` unless it is
recomputed. In the spike this was caught and recalculated by hand (`#484848` →
`#505050`). Relying on catching it by hand every time is not a plan.

## Decision

**A single palette definition file is canonical. Both outputs are generated from it,
and neither generated artifact is ever hand-edited.**

    palettes/grayscale.<def>          ← canonical, hand-authored, the ONLY place
              │                          a palette value is chosen
              ├──→ css/…-palette.css     the --tf-* token block   (generated)
              └──→ theme object          the ~5 seeds + structure (generated)

Derived values (`--tf-line-solid*`, and anything else with a stated formula) are
**computed by the generator**, not stored. The formula lives in code, once, next to a
test asserting it reproduces trimfox's own published values — which it does:
`0.18` over `#202020` → `#484848`, and `0.06` over `#202020` → `#2d2d2d`.

Generated files carry a "do not edit" header naming the source and the generator.

## Consequences

- **Positive: drift becomes structurally impossible**, rather than merely discouraged
  by a comment. This is the same instinct as trimfox-drift, applied one layer earlier
  — prevent the inconsistency instead of detecting it.
- **Positive: derived tokens stop being a manual chore** and stop being a place where
  a careful person can still be wrong.
- **Positive: new palettes stay cheap**, which is the whole point of trimfox's
  swappable-palette design. A `tinted` palette is a new definition file, and `oklch()`
  is confirmed working in the UI layer ([Q5](../vivaldi-research.md)), so the
  parametric palette ports.
- **Positive: it gives the levelset tests ([ADR-0004](0004-settings-recipe-with-levelset-tests.md))
  something precise to assert** — that the installed theme matches the definition.
- **Trade-off: a build step, and generated files in the repo.** trimvaldi stops being
  purely hand-written CSS you can read top to bottom. Mitigated by keeping the
  definition format small and obvious, and by committing the generated output so a
  user can still read and install without running anything.
- **Trade-off: the user-override story needs care.** Users must still override by
  redefining `--tf-*` in `user-overrides.css` and **must never be asked to run the
  generator**. Overriding a token changes our rules immediately; changing the *chrome*
  palette is a theme-level change and is a different, documented operation. This
  distinction did not exist in trimfox and must be stated plainly in the README.
- **Open:** the definition format is not chosen yet. It should be whatever makes the
  file readable as a palette at a glance — legibility across the trimfox/trimvaldi
  family is the reason the `--tf-*` names were kept identical in the first place.
