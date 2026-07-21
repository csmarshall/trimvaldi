# Design ethos → what it actually means as Vivaldi work

Read after `migration-brief.md`. This is the "what are we really signing up for"
document, written to be **checksummed**: every inference is numbered `A1…A13` so
Charles can confirm or reject them individually.

## The decision this rests on

trimvaldi is **not pixel-identical to trimfox**. It is a Vivaldi port carrying the
same **design ethos**. Operationally that means: when trimfox's specific
implementation and Vivaldi's grain disagree, **the ethos wins and the
implementation changes.** We are porting the *reasoning in the ADRs*, not the
appearance of the screenshots.

## The ethos, distilled from trimfox's ADRs

1. **Slim, get-out-of-the-way, power-user-first.** Every chrome element earns its
   space or is trimmed. Optimized for the experienced user, explicitly not the
   general audience the browser rightly designs for. *The tiebreaker for every
   ambiguous call: slimmer, quieter, gets-out-of-the-way wins.* (ADR-0001)
2. **Consolidation over scattered tweaks.** The point is a unified, documented,
   distributable project with a real harness — not a pile of personal hacks.
   (ADR-0001)
3. **The tab strip is the signature.** Collapsed to a thin rail at rest, expanding
   on hover, instantly. At rest it still conveys *shape* — a live tab count read as
   separator lines. (ADR-0002)
4. **A stable `--tf-*` token API over the browser's unstable internals.** Never
   hardcode a colour or size. Colours live in swappable palettes; structure lives in
   dials. Default palette is zero-blue grayscale. (ADR-0005)
5. **Customize without forking.** A gitignored user-override layer applied last,
   winning by plain source order — no `!important`, no merge conflicts on update.
   (ADR-0006)
6. **Opinionated removals, stated plainly.** Affordances get removed and the README
   says so up front rather than surprising people. (README "Heads up")
7. **Accessibility is a floor, not a dial.** `prefers-reduced-motion` forces
   `--tf-anim: 0s` and beats even user overrides.

## Three layers, three very different portability stories

| Layer | Portability | What it costs us |
|---|---|---|
| **A. Philosophy & decisions** (ethos 1, 2, 6, 7) | ~100% | Free. Already written. Copy the reasoning, re-derive the calls. |
| **B. Architecture** (ethos 4, 5) | Portable in *shape*, not mechanism | Medium. The layering idea survives; how it is enforced depends on how Vivaldi loads CSS. |
| **C. The rules themselves** (ethos 3 and everything visual) | ~0% | Full rewrite against a DOM we have not yet seen. |

The palette files are the one happy exception inside layer C — see A5.

## Extrapolation: ethos → real work

### 1. "Trim everything that isn't a tab" → a bigger job here than in Firefox

**A1.** Vivaldi ships **denser default chrome** than Firefox — status bar, panel
rail, extra address-bar controls. So the trim pass is *larger*, not smaller.

**A2.** A meaningful share of that trimming is available as **native Vivaldi
settings**, not CSS. Vivaldi is famously configurable; hiding the status bar or
panel rail is likely a checkbox.

**Consequence if A1+A2 hold:** trimvaldi's deliverable is shaped like trimfox's —
*settings recipe + CSS* — mirroring `user.js` + `userChrome.css`. But **A3:**
Vivaldi settings live in a profile `Preferences` JSON rather than a drop-in file,
so the "prefs" half is probably **documented manual steps or a JSON patch script**,
not an elegant one-file drop. This is a real ergonomics regression versus
`user.js` and worth deciding early.

### 2. The signature tab strip → mostly free, with one genuine design fork

**A4.** Vivaldi has native vertical tabs, so we style rather than construct. If it
*also* offers native collapse + hover-expand, phase 4 shrinks to near nothing; if
not, hover-expand in ordinary CSS (`width` transition on `:hover`) is
**substantially easier than it was in Firefox**.

**The fork — and the most likely place trimvaldi visibly diverges from trimfox:**
in Firefox the expanding sidebar pushes content. Building the same in Vivaldi's
layout would **reflow the page on every hover**, which is jarring and violates
"gets out of the way." The ethos-faithful answer is probably to **overlay** the
expanded strip over content rather than push it. Same ethos, different mechanic,
different look. This is exactly the kind of call the not-pixel-identical decision
is meant to license.

Reproducing "a live tab count as separator lines" means hiding favicon/label/close
in the collapsed state and rendering a per-tab separator — feasible, but it is a
**deliberate rebuild of a look**, not a port.

### 3. The token architecture → the dependency direction *flips*

This is the most important structural insight and the least obvious.

In trimfox, the theme **consumes** Firefox's private variables and maps them onto
`--tf-*`. The fragility is therefore **variable renames**, which is precisely what
`trimfox-drift` watches, and why it works: variable names are greppable.

In Vivaldi, we are not consuming a private variable set the same way — we are
**setting** properties on a DOM we select into. **A6:** the churn surface moves
from *variable names* to *selectors and DOM structure*.

**Consequence:** trimvaldi's drift is **harder to monitor and more likely to fail
silently** — a renamed class doesn't error, it just quietly stops applying. A
Firefox var rename tends to produce something visibly wrong; a dead CSS rule
produces something subtly un-themed.

**A7.** Therefore: **centralize every Vivaldi selector in one file**, the same way
trimfox centralized the Firefox-var→token mapping. Cheap now, expensive to retrofit,
and it is the precondition for any future `trimvaldi-drift`. I would treat this as
an architectural requirement from the first line of CSS, not a later tidy-up.

### 4. The palette → the single biggest genuine reuse

**A5.** `grayscale.css` is **plain hex and rgba with no Firefox specifics** — it
should port very nearly verbatim, as should `tinted.css`, since Chromium has
supported `oklch()` since 111. Realistically this is the one file we mostly copy.

**A8.** But light/dark switching may not port. trimfox keys off
`prefers-color-scheme`, which follows macOS appearance. Vivaldi has **its own theme
system**, including scheduled light/dark. If a user sets a Vivaldi theme
independently of the OS, `prefers-color-scheme` could disagree with the browser's
own idea of light or dark. Needs verifying (research Q3); it may force us to key off
Vivaldi's theme state instead, which in turn pressures the "drive vs bypass the
theme engine" decision toward **driving** it.

### 5. The override layer → likely *better* than trimfox's

**A9.** trimfox's override contract relies on **source order** (overrides imported
last). That only works if we control load order. If Vivaldi loads a folder of `.css`
files in unspecified order, source order is not guaranteed — so we would need a
single entry file using `@import`.

**A10.** Better: **CSS cascade layers (`@layer`)** are well supported in Chromium
and make the contract explicit and order-independent —
`@layer dials, palette, theme, overrides;`. This is a genuine *improvement* over
trimfox's mechanism, and I would take it. The user-facing promise ("your file wins,
no `!important`, `git pull` never conflicts") is preserved exactly; only the
enforcement gets more robust.

### 6. The opinionated removals → re-decide, do not copy

**A11.** trimfox's combined history-aware back/forward button is the *implementation*
of an ethos ("one control, history on right-click, reclaim the space"). Vivaldi's
navigation controls and its own history affordances differ, so the right move is to
**re-derive** that decision against Vivaldi's grain rather than reproduce the
chevron behaviour literally. Same principle, possibly a different control.

### 7. Maintenance posture

**A12.** Vivaldi UI mods may **not survive application updates** (research Q6). If
so, that is a prominent README warning and possibly a re-apply script — a
maintenance burden trimfox does not carry in the same form.

**A13.** ADRs should start at **0001 in this repo**, not continue trimfox's
numbering, but each should cite its trimfox ancestor. The reasoning is inherited;
the decisions are being made fresh against a different browser.

## What I would want confirmed before writing any CSS

Ranked by how much rework a wrong answer causes:

1. **A7** (centralize selectors from day one) — architectural, expensive to retrofit.
2. **A10** (use `@layer` instead of source order) — architectural, easy now.
3. **The overlay-vs-push fork** in §2 — defines the signature look.
4. **A2/A3** (settings recipe as part of the deliverable) — defines project scope.
5. **A8** (light/dark source of truth) — forces the theme-engine decision.

Everything else can be resolved as the DOM becomes visible.
