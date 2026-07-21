# ADR-0005 — The hover-expanded tab strip overlays content rather than pushing it

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0002 — Collapse / expand-on-hover](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0002-collapse-expand-on-hover.md)

## Context

The collapsed strip that expands on hover is trimfox's signature — the trim,
get-out-of-the-way ethos made concrete, and the single most recognizable thing about
it. Carrying it over is non-negotiable.

*How* it expands is negotiable. In Firefox, the native sidebar **pushes** page content
aside as it widens. Reproducing that literally in Vivaldi would reflow the page on
**every hover** of a ~14px target — content jumping sideways as the pointer passes
through. That is the opposite of getting out of the way, and the strip is on the edge
of the window where the pointer travels constantly.

Vivaldi may or may not offer collapse + hover-expand natively
([`../vivaldi-research.md`](../vivaldi-research.md) Q4). Either way the push-vs-overlay
behaviour is a decision we make, not one we inherit.

## Decision

**The expanded strip overlays page content.** The layout reserves only the collapsed
width; expansion floats above the page and reflows nothing.

Under [ADR-0001](0001-ethos-faithful-port.md) this is exactly the licensed case: it
diverges visibly from trimfox's behaviour *because* it serves trimfox's stated ethos
better on this browser. Nothing moves that the user did not ask to move.

## Consequences

- **Positive:** zero reflow on hover; page content never shifts under the pointer.
- **Positive:** arguably *more* get-out-of-the-way than the original — the strip costs
  its collapsed width permanently and nothing more, ever.
- **Positive:** decouples the strip from page layout, which should simplify the CSS
  (no layout participation to fight) and sidestep whatever Vivaldi's own tab-bar
  sizing does.
- **Trade-off:** visibly different from trimfox for anyone running both. Expected and
  intended under ADR-0001, but it belongs in the README rather than being discovered.
- **Trade-off:** an overlay covers content, so the strip needs enough contrast and
  likely a shadow or edge to read as floating rather than as part of the page — new
  visual work the pushing version did not require, and it must hold on both the
  grayscale and tinted palettes.
- **Trade-off:** if Vivaldi's native vertical tabs push and cannot be made to overlay,
  this decision may cost real effort or force a revisit. Unverified — Q4.
