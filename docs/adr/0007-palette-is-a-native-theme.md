# ADR-0007 — The palette is a native Vivaldi theme, not a stylesheet

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0005 — `--tf-*` token API and swappable palettes](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0005-token-api.md)
- **Closes:** [`../vivaldi-research.md`](../vivaldi-research.md) Q3, and assumption **A5**
  in [`../design-ethos.md`](../design-ethos.md)

## Context

trimfox recolours Firefox by mapping `--tf-*` tokens onto Firefox's chrome variables
in a stylesheet. The obvious port was to do the same to Vivaldi's `--color*` variables,
and `design-ethos.md` A5 predicted the palette files would be "the one file we mostly
copy". The open question (Q3) was framed as **drive Vivaldi's theme engine, or bypass
it** — both understood as things one would do *in CSS*.

**The spike showed that framing had a false premise.** Measured against 8.1.4087.55:

Vivaldi's theme engine computes the palette in JavaScript and writes **all ~117
`--color*` properties as a single ~5,306-character inline `style` attribute on
`#browser`**. Inline styles beat all author CSS regardless of specificity. So a
stylesheet cannot recolour Vivaldi at all without `!important` on every mapped
variable — verified empirically: our CSS mapping layer silently did nothing,
`--colorBg` stayed `#363536`, and Vivaldi's `#7aa0ff` blue survived untouched.

But those 117 variables are **derived**, by the engine, from a theme object of only
about **five seed colours** plus structural knobs:

    colorBg  colorFg  colorAccentBg  colorHighlightBg  colorWindowBg
    + accentFromPage, backgroundImage, blur, alpha, radius, …

And themes are ordinary prefs — `vivaldi.themes.user`, `vivaldi.themes.current`,
`vivaldi.theme.schedule.o_s` — so defining one is fully scriptable, which keeps the
zero-GUI-step install property intact ([ADR-0004](0004-settings-recipe-with-levelset-tests.md)).

## Decision

**The palette ships as a native Vivaldi theme, installed via prefs. CSS is not used
to recolour Vivaldi's chrome.**

CSS keeps only the jobs it is actually good at here: structure, layout, trimming, and
the `--tf-*` token vocabulary used by *our own* rules.

Two ethos wins come free, as theme properties rather than separate settings:

    accentFromPage: false   kills .color-accent-from-page — Vivaldi tinting its chrome
                            from the page's theme colour, the single most hostile
                            default to zero-blue grayscale. CONFIRMED off.
    backgroundImage: ""     removes the chrome background image (bg_dark-8.png), for
                            the flat surfaces trimfox assumes.

## Consequences

- **Positive: far less code.** Five seed colours replace mapping ~40 variables, and
  the engine derives the Dark/Darker/Light/Faded/Alpha family for us, consistently.
- **Positive: immune to selector churn.** This is the concern [ADR-0002](0002-centralize-selectors.md)
  exists to manage, and the palette layer now sidesteps it entirely — there are no
  selectors in a theme object.
- **Positive: no `!important` needed for colour.** The stylesheet route would have
  required it on every declaration, contradicting the promise inherited from trimfox.
- **Positive: hue is preserved.** Verified — from exactly-neutral seeds, every derived
  variable came back exactly neutral (R=G=B) in both light and dark. Zero-blue
  survives derivation, so we never need Vivaldi's hues to get a coherent ramp.
- **Trade-off: we inherit the engine's derivation curve.** We choose five colours; it
  chooses the other 112. Where its idea of "Darker" disagrees with ours, the escape
  hatch is a specificity-matched CSS override, not a redefinition.
- **Trade-off: the derivation assumes headroom below `colorBg`.** At trimfox's
  `#202020` the bottom rung clipped to pure `#000000`. Resolved by lifting the whole
  dark ramp uniformly by +10, preserving trimfox's gaps (10/4/14/39) rather than its
  absolute values. **We take Vivaldi's luminance headroom, never its cast** — its own
  base `#363536` is non-neutral and its `colorFg #d3d9e3` is openly blue.
- **Trade-off: the palette now has two representations** — theme seeds and `--tf-*`
  CSS tokens — which must agree or drift silently. Addressed by
  [ADR-0008](0008-one-palette-definition.md).
- **Gotcha to encode in the installer:** `vivaldi.theme.schedule.enabled` defaults to
  `system`, and while it is, the OS appearance **overrides `vivaldi.themes.current`**.
  Set the `o_s` light/dark map as well, or the active theme silently will not be the
  one selected.
- **Lesson recorded:** the question was posed as a binary ("drive or bypass") and the
  answer was neither — *drive it, but through a different interface than the one we
  assumed existed*. Worth remembering the next time an option list feels complete.
