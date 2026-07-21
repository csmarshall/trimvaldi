# ADR-0003 — Enforce the override contract with CSS cascade layers

- **Status:** ⚠️ **SUPERSEDED by [ADR-0006](0006-import-order-not-cascade-layers.md)** (2026-07-21, same day)
- **Date:** 2026-07-21

> **Do not implement this.** The reasoning below is sound but rests on a premise that
> turned out to be false. Vivaldi's UI stylesheet is entirely **unlayered** author CSS
> (verified: `style/common.css`, 1023K, zero `@layer` in 8.1.4087.55), and unlayered
> normal declarations beat *all* layered ones within an origin — so a layered trimvaldi
> would lose every conflict with Vivaldi's own defaults, regardless of specificity.
> Kept as a record so the option is not re-proposed. See ADR-0006.
- **Ancestor:** trimfox [ADR-0006 — `user-overrides` layer](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0006-user-overrides-layer.md)

## Context

trimfox's promise to users: *your overrides win, with plain declarations, no
`!important`, and `git pull` never conflicts with your colours.* It delivers that
through **source order** — `user-overrides.css` is `@import`ed last, so it is simply
the final word.

Source order only works if we control load order. In Vivaldi we may not: the custom
UI mechanism appears to load a *folder* of `.css` files, and the order is not
something we have confirmed we can dictate (see
[`../vivaldi-research.md`](../vivaldi-research.md) Q1). If load order is
alphabetical, arbitrary, or subject to change, the entire contract is quietly
unreliable — and it would fail in the worst way, by working during development and
breaking for some users.

Chromium has solid support for **CSS cascade layers**, which express precedence
explicitly rather than positionally.

## Decision

Declare the precedence up front and assign every stylesheet to a layer:

```css
@layer dials, palette, theme, overrides;
```

Later layers beat earlier ones **regardless of file load order or selector
specificity**, so `overrides` wins by construction rather than by accident of
sequencing.

The user-facing promise is unchanged and exact: your file wins, plain declarations,
no `!important`, no merge conflicts. Only the enforcement mechanism is different —
and stronger.

## Consequences

- **Positive:** the contract holds even if Vivaldi loads files in an order we do not
  control, which is the specific risk that motivated this.
- **Positive:** precedence is *declared and readable* in one line instead of being an
  emergent property of `@import` sequencing — a subtlety trimfox's own ADR-0006 flags
  as something contributors must know.
- **Positive:** layers also beat specificity, so an override no longer has to match
  the specificity of the rule it is replacing.
- **Trade-off:** diverges from trimfox's mechanism, so the two repos are no longer
  conceptually identical on this point — someone who knows trimfox's source-order
  trick has one new thing to learn. Documented in both the README and `css/README.md`.
- **Trade-off:** unlayered CSS beats *all* layered CSS in the cascade, so nothing in
  the project may be left unlayered by accident. Worth a note for contributors.
