# ADR-0001 — Ethos-faithful port, not a pixel-identical reproduction

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0001 — Design philosophy](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0001-design-philosophy.md)

## Context

trimvaldi exists to bring [trimfox](https://github.com/csmarshall/trimfox)'s look and
feel to Vivaldi. But Vivaldi has no `userChrome.css`: its UI is an ordinary Chromium
web app, sharing zero selectors, zero chrome variables, and zero install mechanics
with Firefox's XUL chrome. Nothing mechanical transfers.

That leaves a choice. Either chase pixel-parity with trimfox — reconstructing its
exact appearance on a browser whose affordances differ — or carry across the
*reasoning* and let the implementation follow Vivaldi's grain.

Pixel-parity is the more seductive goal and the worse one: it means fighting the
application, and it optimizes for resemblance to a screenshot rather than for the
thing the screenshot was trying to achieve.

## Decision

**trimvaldi is ethos-faithful, not pixel-faithful.**

Where trimfox's specific implementation and Vivaldi's grain disagree, **the ethos
wins and the implementation changes.** We port the reasoning in trimfox's ADRs, not
the appearance of its screenshots.

The ethos being ported, distilled from trimfox's ADRs:

1. Slim, get-out-of-the-way, power-user-first — every element earns its space.
   The tiebreaker for any ambiguous call: *slimmer, quieter, gets-out-of-the-way wins.*
2. Consolidation over scattered tweaks — one unified, documented, distributable
   project with a real harness.
3. The tab strip is the signature — collapsed at rest, expanding on hover, instantly,
   still conveying shape at rest.
4. A stable `--tf-*` token API over the browser's unstable internals; never hardcode.
5. Customize without forking — a user-override layer that wins without `!important`.
6. Opinionated removals, stated plainly rather than sprung on people.
7. Accessibility is a floor, not a dial — reduced-motion beats even user overrides.

## Consequences

- **Positive:** frees us to make Vivaldi-native calls that serve the ethos better
  than a literal port would — see [ADR-0005](0005-hover-expand-overlays.md), where
  overlaying beats trimfox's push precisely *because* it gets further out of the way.
- **Positive:** trimfox's ADRs become reusable reasoning rather than a spec to match,
  so decisions get re-derived against the actual browser instead of inherited blindly.
- **Trade-off:** trimvaldi will not look identical to trimfox, and side-by-side
  screenshots will differ. That is intended and should be stated in the README rather
  than read as incompleteness.
- **Trade-off:** "does this serve the ethos?" is a judgement call, so decisions need
  recording (these ADRs) or they will be re-litigated.
