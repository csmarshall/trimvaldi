# ADR-0006 — Override contract via controlled import order, not cascade layers

- **Status:** Accepted — **supersedes [ADR-0003](0003-cascade-layers-override.md)**
- **Date:** 2026-07-21
- **Ancestor:** trimfox [ADR-0006 — `user-overrides` layer](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0006-user-overrides-layer.md)

## Context

[ADR-0003](0003-cascade-layers-override.md) chose CSS cascade layers to enforce the
override contract, on the reasoning that `@layer` is order-independent and therefore
survives not controlling how Vivaldi loads a CSS folder. That reasoning was sound.
The premise was not.

**Verified against Vivaldi 8.1.4087.55** (installed 2026-07-21):

    Resources/vivaldi/style/common.css   — 1023K, the UI theme
    grep -c '@layer'                     — 0

Vivaldi's entire UI stylesheet is **unlayered author CSS**.

That matters because of how the cascade sorts within an origin. For **normal**
declarations, unlayered styles have *higher* precedence than **all** layered styles,
regardless of specificity:

    normal:  unlayered  >  last layer  >  …  >  first layer

Our injected CSS lands in the same author origin as Vivaldi's own. So a fully-layered
trimvaldi would **lose every conflict with Vivaldi's defaults** — not occasionally,
but categorically, and specificity could not rescue it. The theme would effectively
not apply.

The only escape inside a layered design is `!important` on essentially every
declaration, which directly contradicts the promise inherited from trimfox's ADR-0006:
*plain declarations, no `!important`.*

ADR-0003's stated sharp edge — "nothing may be left unlayered by accident" — was
therefore backwards. The hazard was not our own unlayered CSS winning; it was
**Vivaldi's** unlayered CSS beating all of ours.

## Decision

**Stay unlayered, and guarantee precedence by controlling load order explicitly.**

A single entry stylesheet `@import`s everything in a fixed sequence:

    @import url("selectors.css");        /* ADR-0002 — the sole place Vivaldi's DOM is named */
    @import url("dials.css");            /* structural defaults */
    @import url("palettes/grayscale.css");
    @import url("trimvaldi.css");        /* the theme */
    @import url("user-overrides.css");   /* user-owned, gitignored, LAST */

This is trimfox's mechanism, adopted deliberately rather than inherited by default.
It solves the original worry a different way: the risk was never source order *as an
idea*, it was not controlling the order. One entry file controls it completely,
whatever order Vivaldi walks a folder in.

**Why plain source order is sufficient here** — and this is the part worth
understanding rather than memorizing: the override surface is the **token
vocabulary**, not arbitrary rules. Users override by redefining `--tf-*` custom
properties on `:root`. Two `:root` blocks have identical specificity, so the later one
wins on source order alone, deterministically. The token architecture
([ADR-0002](0002-centralize-selectors.md); trimfox ADR-0005) is precisely what makes
source-order overriding sound. The two decisions hold each other up.

## Consequences

- **Positive:** the theme can actually beat Vivaldi's defaults — competing on ordinary
  specificity and source order, exactly as trimfox competes with Firefox's chrome CSS.
- **Positive:** restores conceptual parity with trimfox. Someone who understands one
  repo's override model understands the other's; ADR-0003 had listed losing that as a
  trade-off.
- **Positive:** the ADR-0003 sharp edge disappears entirely. There is no layer to
  forget to declare.
- **Positive:** the user-facing promise is unchanged and unchanged in mechanism — your
  file loads last and wins, no `!important`, `git pull` never conflicts.
- **Trade-off:** source order only breaks ties at *equal* specificity, so overriding a
  raw rule (rather than a token) requires matching its specificity. This is the exact
  cost trimfox already pays, and the token architecture keeps it off the common path.
- **Trade-off:** depends on being able to load a single entry file that `@import`s the
  rest. **Confirmed available** — see the verification section below.
- **Lesson recorded:** ADR-0003 was decided on a plausible assumption about someone
  else's codebase and was wrong within hours of being checkable. Verify the premise
  before the architecture, not after.

## Verification — spike, 2026-07-21, Vivaldi 8.1.4087.55

Everything above was reasoning. This section is measurement. See
[`../../spike/README.md`](../../spike/README.md).

### The load-order premise holds, and better than assumed

`chrome://vivaldi-data/css-mods/css` is **not a concatenation**. It is a generated
stylesheet of one `@import` per `.css` file in the folder, **in alphabetical order**:

    @import url("00-alpha.css");
    @import url("99-omega.css");

So both routes work: a single entry file `@import`ing the rest, *and* plain numeric
filename prefixes. `@import` demonstrably resolves from that `chrome://` endpoint.
**Q1 is closed.** The decision above stands unchanged.

### The specificity trade-off is real, and it fails SILENTLY

The trade-off listed above was written as theory. It bit immediately:

    #tabs-tabbar-container { background: #c00 }                     ← ours, (1,0,0). LOST.
    #browser:not(.transparent-tabbar) #tabs-tabbar-container { … }  ← Vivaldi's, (2,1,0)

No error, no warning — the rule simply had no effect, and the natural conclusion was
"our CSS isn't loading" when in fact it was. This is exactly the failure mode
[ADR-0002](0002-centralize-selectors.md) exists to contain, and it is a strong
argument for keeping every Vivaldi selector in one reviewable file.

**Restated plainly: source order lets our tokens beat OUR OWN defaults. It does not
let our rules beat VIVALDI'S.** Those are different claims and only the first is
guaranteed.

### One unavoidable `!important` — Vivaldi's inline styles

The "no `!important`" promise cannot be kept absolutely, because Vivaldi writes some
values as **inline style attributes**, which beat all author CSS:

- `#tabs-tabbar-container` gets `style="width: 360px"` from `vivaldi.tabs.bar.width`.
  Collapsing the strip therefore *requires* `!important`. No selector avoids it.
- The theme engine writes ~117 `--color*` properties as a single ~5KB inline `style`
  on `#browser`. **This one we route around rather than override:** the palette
  installs as a native Vivaldi theme via prefs, so no CSS override is needed at all.

**The user-facing contract survives**, because the `!important` sits on a rule whose
*value* is a token — a user redefining `--tf-strip-collapsed` in `user-overrides.css`
still wins. The promise should be stated as *"you never need `!important` to override
trimvaldi"*, which remains true, rather than *"trimvaldi contains no `!important`"*,
which is now false.
