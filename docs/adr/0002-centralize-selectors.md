# ADR-0002 — Centralize every Vivaldi selector in one file

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0005 — `--tf-*` token vocabulary](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0005-tf-token-palette-architecture.md), [ADR-0007 — trimfox-drift](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0007-trimfox-drift-monitor.md)

## Context

trimfox **consumes** Firefox's private theme variables and maps them onto `--tf-*`
tokens. Its fragility is therefore concentrated in **variable renames** — and that
is a tractable problem: variable names are greppable, which is exactly what makes
`trimfox-drift` possible, and a broken mapping usually looks visibly wrong.

In Vivaldi the dependency direction **flips**. We are not consuming a private
variable set the same way; we are *setting* properties on a DOM we select into. The
churn surface moves from **variable names to selectors and DOM structure**.

That is a worse failure mode. A renamed CSS class does not error — it silently stops
applying. Where a Firefox variable rename tends to produce something obviously
broken, a dead Vivaldi selector produces something *subtly un-themed*, which can sit
unnoticed for a long time.

## Decision

**Every Vivaldi selector lives in exactly one file**, from the first line of CSS.
Theme rules never name Vivaldi's DOM directly; they reference semantic aliases
defined in that single file.

This mirrors what trimfox did with the Firefox-var → `--tf-*` mapping: concentrate
the unstable, foreign surface in one auditable place, and keep the rest of the theme
written against a stable vocabulary we own.

It is also the **precondition for any future `trimvaldi-drift`** — a monitor can only
check a dependency surface that is enumerable in one place.

## Consequences

- **Positive:** a Vivaldi UI restructure becomes a one-file fix instead of a hunt
  through scattered rules.
- **Positive:** the dependency surface is enumerable, so it can be tested and
  monitored. Without this there is no monitoring story at all.
- **Positive:** the theme reads in trimvaldi's own vocabulary rather than Vivaldi's
  internal one, which keeps it legible next to trimfox.
- **Trade-off:** a layer of indirection between the CSS and the DOM it targets, and
  the discipline to never reach around it. Same tax trimfox pays for its token layer,
  taken deliberately for the same reason.
- ~~**Open:** how aliasing is expressed in practice~~ — **RESOLVED by
  [ADR-0009](0009-selector-registry-and-verifier.md)** (2026-07-22): plain CSS, no
  build step, with a machine-readable registry in `css/00-selectors.css` live-checked
  by `tools/verify-selectors.py`. The guess above was close — a documented block of
  grouped definitions with a strict convention — but missed two things the real DOM
  showed. Each entry needs the browser **state** it requires, or state-dependent
  selectors read as renames; and Vivaldi's **variable names are a second foreign
  surface**, more dangerous than selectors because a variable can exist with a wrong
  value and fail silently at the value level rather than the name level.
