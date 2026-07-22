# ADR-0009 — Selector centralization via a registry and a live verifier

- **Status:** Accepted
- **Date:** 2026-07-22
- **Resolves:** the **Open** question in [ADR-0002](0002-centralize-selectors.md) —
  "how aliasing is expressed in practice (CSS custom properties cannot hold
  selectors) … resolved once the real DOM is visible"
- **Ancestor:** trimfox [ADR-0007 — trimfox-drift](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0007-trimfox-drift-monitor.md)

## Context

[ADR-0002](0002-centralize-selectors.md) requires every Vivaldi selector to live in
one file, because that surface **fails silently**: a renamed class does not error, it
quietly stops applying, and the result reads as "slightly un-themed" rather than
broken. It deliberately left the *mechanism* open, because CSS cannot alias a selector
the way a custom property aliases a value.

The options, once the DOM was visible:

1. **A CSS build step** (Sass/PostCSS) with selector variables, so theme rules write
   `#{$tf-strip}`. True aliasing, structurally enforced — but the shipped CSS stops
   being readable as source, which ADR-0002 itself lists as a *benefit* of
   centralizing ("keeps it legible next to trimfox").
2. **Convention only** — one file owns the DOM-targeting rules, enforced by review.
   Cheapest, and leaves the exact silent-drift failure mode ADR-0002 exists to stop.
3. **Convention plus a machine-checkable registry.**

Two discoveries during the spike made option 3 clearly right.

**First, a naive checker produces false alarms.** `.BookmarkButton` is absent on
`about:blank` and present on a real page. A tool that only asks "does this selector
match?" reports a rename that never happened, and a tool that cries wolf gets ignored.
So the registry must record **what state each selector requires**.

**Second, there are two foreign surfaces, not one.** Vivaldi's *variable* names are a
dependency too — and a more dangerous one than expected, because a variable can exist
with a **wrong value**. Measured on 8.1.4087.55:

    --colorBorder   #181818  DARKER than the surface; trimfox's line is LIGHTER
                             (#505050). Opposite polarity — separators would have
                             rendered as dark grooves.
    --colorFgFaded  #f2f2f2  vs trimfox's #aaaaaa. Not dim by any measure.

Neither would have errored. Both would have looked *nearly* right.

## Decision

**Plain CSS, no build step for selectors. `css/00-selectors.css` is the only file that
names Vivaldi's DOM or Vivaldi's variables; every other file in `css/` is token-only.
A machine-readable registry in that file's header is live-checked by
`tools/verify-selectors.py`.**

    @sel  <name> | <selector>      | <requires>
    @var  <name> | <--vivaldi-var> | <requires>

`<requires>` is the browser state an entry needs (`always`, `tabs-left`,
`theme-light`, `page-loaded`, or `never`). Entries whose state the current run cannot
satisfy are **skipped, not passed** — the tool says so explicitly, because a skip that
reads as a pass is worse than no check.

`never` asserts an entry stays *absent*. It exists for `--colorTabBar`, which Vivaldi
references but never defines (`var(--colorTabBar, transparent)`) — an open hook we
rely on, so we want to know if Vivaldi ever starts setting it itself.

Only lines between `@registry-begin` and `@registry-end` are parsed, so the format
documentation above the registry does not register itself.

## Consequences

- **Positive: the dependency surface is enumerable and checked**, which is the
  precondition ADR-0002 named for any future `trimvaldi-drift`. The monitor is now a
  thin wrapper around this tool rather than a project of its own.
- **Positive: it works.** Vivaldi auto-updated 8.1.4087.55 → **.56** during the
  session that built it, and the verifier ran green against the new build unprompted —
  23 ok, 0 failed. First real test, unplanned, passed.
- **Positive: the CSS stays hand-readable**, no second build step beyond ADR-0008's
  palette generator.
- **Positive: aliasing by VALUE, not just name.** Registering variables forced us to
  compare values against trimfox's intent, which is what caught `--colorBorder`'s
  inverted polarity. A name-only check would have missed it.
- **Trade-off: enforcement is a tool, not the language.** Nothing physically stops
  someone typing a Vivaldi class into another file; the convention plus review plus
  the verifier is what holds. Accepted as the price of readable CSS.
- **Trade-off: the registry must be maintained by hand** alongside the rules. Mitigated
  by it being short — currently 23 entries, and only **two** Vivaldi variables, which
  we deliberately keep minimal.
- **Sharp edge, learned the hard way: CSS comments do not nest.** Quoting Vivaldi's own
  CSS inside an explanatory comment introduced an inner `*/` that closed the block
  early and **silently dropped the following rule**. The symptom was indistinguishable
  from "my override lost on specificity". Never paste CSS containing comments into a
  comment.
- **Sharp edge: the css-mods endpoint caches.** Editing a file and reloading the UI
  does **not** pick up changes; the browser must be restarted. Costly to rediscover.
