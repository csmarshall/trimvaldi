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
- ~~**Open:** the definition format is not chosen yet.~~ **RESOLVED 2026-07-22 — a
  commented INI**, `palettes/<name>.ini`.

  TOML would have been the obvious pick, but `tomllib` needs Python 3.11 and the
  repo's other tools run on the system 3.9. JSON is stdlib but has **no comments**,
  and trimfox's palettes are heavily commented — they explain *why* each colour is
  what it is. Losing that would be a real regression in exactly the legibility this
  ADR is trying to protect, so a format was chosen that keeps it.

## Implementation notes — 2026-07-22

`tools/build-palette.py`. Three token classes, and the generator **enforces** the
split so a value cannot quietly end up defined twice:

    ALIASED  Vivaldi supplies it exactly → aliased from --colorBg / --colorFg in
             00-selectors.css. Gets light/dark switching free, since Vivaldi swaps
             the seeds itself. (surface, text)
    DERIVED  trimfox states a formula → computed with color-mix() in
             00-selectors.css. Putting one of these in the .ini is a HARD ERROR:
             that is precisely the second source of truth this ADR removes.
             (line, line-inactive, line-solid, line-solid-inactive, highlight)
    EMITTED  no close-enough Vivaldi equivalent and no stated formula → written to
             css/20-palette.css. (raised, text-dim, field, content, select,
             accent*, glyph, attention, highlight-inactive)

The derivation formula ships with a **regression test against trimfox's own
published values**, run on every generate — 18% white over `#202020` must give
`#484848` and 6% must give `#2d2d2d`, exactly. If it ever stops matching, the
generator refuses to run, because silently redefining what trimfox means by a
separator line is the failure this is guarding.

`--check` verifies the committed outputs match the definition and exits non-zero
if not, so a hand-edit of a generated file is caught rather than absorbed.
`tools/apply-settings.py` reads the generated theme JSON rather than carrying its
own copy of the seeds — otherwise the tool most able to cause the drift would be
the one blind to it.

**Verified end to end:** all four guards fire (derived-token-in-definition,
mismatched light/dark token sets, hand-edited output, stale-on-check), and the
live browser resolves aliased, derived and generated tokens together with
`--tf-raised: #383838` and `--tf-text-dim: #aaaaaa` matching trimfox exactly.
