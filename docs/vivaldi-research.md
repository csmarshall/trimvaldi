# Vivaldi research — verification log

**Reference build:** Vivaldi **8.1.4087.56** (arm64 macOS) on `toad`, installed via
`brew install --cask vivaldi` on 2026-07-21 as 8.1.4087.55 and **auto-updated to .56
on 2026-07-22 mid-session** — which is how Q6 got answered. Findings below were
measured against .55 unless noted; the selector surface was re-verified green against
.56.

Items are marked `VERIFIED` with evidence, or `OPEN` where still unconfirmed. Do not
cite an `OPEN` item as fact.

> **Updated 2026-07-21 after the feasibility spike** ([`../spike/README.md`](../spike/README.md)):
> Q1, Q3, Q5 and Q7 closed by measurement.
>
> **Updated 2026-07-22: Q6 is now ANSWERED too** — Vivaldi auto-updated mid-session
> against a modded profile and everything survived. Scope that claim to *routine*
> updates; see Q6. **Q2 is the only substantially open item left.**

## The second most useful discovery — `prefs_definitions.json`

    Resources/vivaldi/prefs_definitions.json

An **authoritative registry of 618 prefs, with types and defaults.** This supersedes
grepping the JS bundle for pref *names*, because it also gives the **type** — and type
is what silently broke Q7 for a whole session. Read it before writing any pref:

```sh
python3 -c 'import json;d=json.load(open("prefs_definitions.json"));…'   # see spike/
```

It is also the natural input to [ADR-0004](adr/0004-settings-recipe-with-levelset-tests.md)'s
levelset tests: expected type and default, per pref, straight from the build.

## The single most useful discovery

**Vivaldi ships its entire UI unpacked and readable on disk.** No archive to extract,
no devtools required for static recon:

    /Applications/Vivaldi.app/Contents/Frameworks/Vivaldi Framework.framework/
      Versions/<version>/Resources/vivaldi/          ← version dir changes on update!
        window.html          the UI entry point
        style/common.css     1023K — the entire UI theme
        components/          per-feature CSS

This is a materially better position than trimfox had with Firefox, where chrome CSS
lives inside `omni.ja` and had to be unzipped to inspect. Here the whole dependency
surface is greppable directly. Devtools remain necessary for *live DOM* confirmation
(the CSS may contain legacy or unused selectors), but selector discovery is now a
`grep`.

## Q1 — How are custom UI CSS mods injected? `VERIFIED — fully closed`

`window.html` contains exactly two stylesheet links, in this order:

```html
<link rel="stylesheet" href="style/common.css" />
<link rel="stylesheet" href="chrome://vivaldi-data/css-mods/css" />
```

**This is decisive for the override architecture.** The mod endpoint is a supported,
built-in `<link>` — not a hack — and it loads **after** Vivaldi's own stylesheet, in
the same author origin. Plain source order and ordinary specificity therefore work in
our favour, exactly as trimfox's CSS competes with Firefox's chrome CSS. This is the
empirical basis for [ADR-0006](adr/0006-import-order-not-cascade-layers.md).

### CLOSED 2026-07-21 — the endpoint emits `@import`, alphabetically

The folder is **user-chosen**, pointed at by exactly one pref:

    vivaldi.appearance.css_ui_mods_directory   (type: file_path)

and that pref is **the only load-bearing setting**. Measured with two negative
controls: with the directory pref absent, mods do not load; with it present but the
`vivaldi-css-mods` experiment flag deliberately absent, they **do** load.

> ⚠️ **The experiment flag is NOT required on 8.1.4087.55**, and
> `vivaldi.features.css_mods` — which [vivaldi-peek](https://github.com/xpltdco/vivaldi-peek)
> documents — **does not exist anywhere in this build**, neither in the UI bundle nor
> in the framework binary. Do not copy that recipe verbatim. The flag that *does*
> exist is the chrome://flags-style entry `vivaldi-css-mods`, stored in **Local State**
> under `browser.enabled_labs_experiments`, and it appears to be vestigial here.

The endpoint does **not** concatenate. It generates a stylesheet of one `@import` per
`.css` file, in **alphabetical order**:

    @import url("00-alpha.css");     → chrome://vivaldi-data/css-mods/00-alpha.css
    @import url("99-omega.css");

So load order is controllable **both** by filename prefix and by a single entry file,
and `@import` resolves from the `chrome://` endpoint. ADR-0006 is safe either way.

**Gotcha when introspecting:** imported sheets are *not* members of
`document.styleSheets`. Recurse via `rule.styleSheet`, or you will wrongly conclude
your own rules never loaded.

## Q2 — The UI DOM and its selectors `PARTIALLY VERIFIED`

Real class names confirmed present in `common.css`:

    .tab  .tab-group  .tab-count  .tab-header  .tab-mini  .tab-indicator
    .tab-audio  .tab-captured  .tab-dropzone  .tab-first-in-group  .tab-accordion

Note these are **Vivaldi's actual names**, and they bear no resemblance to Firefox's
(`.tabbrowser-tab`, `#urlbar`, `.urlbarView-row`) — the zero-shared-selectors premise
of [ADR-0001](adr/0001-ethos-faithful-port.md) is now confirmed rather than assumed.

**Still OPEN:** which of these appear in the live DOM versus being legacy, the full
tree for vertical-tab mode, and the address bar / panel structure. Requires devtools
against a running window.

## Q3 — Vivaldi's theme variables `VERIFIED — drive the engine, via PREFS not CSS`

A substantial custom-property theme system, e.g.:

    --colorBg          --colorFg          --colorAccentBg     --colorAccentFg
    --colorBgDark      --colorBgAlpha     --colorAccentBgFaded  --colorAccentBorder
    (plus Alpha / Faded / Dark / Darker / Heavy variants throughout)

### CLOSED 2026-07-21 — and the answer is not the one we were choosing between

**117 such properties are live on `#browser`** — a rich hook surface, structurally
the same shape as trimfox mapping `--tf-*` onto Firefox's chrome variables.

But the framing "drive the engine *or* bypass it" had a false premise. Vivaldi's theme
engine computes the palette in JS and writes all 117 as a single **~5,306-character
inline `style` attribute on `#browser`**. Inline styles beat all author CSS, so:

- **Recolouring from a stylesheet is not viable** — it needs `!important` on every
  mapped variable. Verified: our CSS map silently did nothing; `--colorBg` stayed
  `#363536` and Vivaldi's `#7aa0ff` blue survived untouched.
- **But the 117 are DERIVED from a theme object of ~5 seed colours.** So the palette
  installs as a **native Vivaldi theme**, written to prefs:

      vivaldi.themes.user        list of theme objects
      vivaldi.themes.current     id of the active one
      vivaldi.theme.schedule.o_s {"light": <id>, "dark": <id>}

**Decision: drive the theme engine, through prefs rather than CSS.** Less code, immune
to selector churn, still zero GUI steps. CSS is then left to do only what it is
actually good at here — structure and trimming.

Two ethos wins come free as theme properties rather than separate settings:

    accentFromPage: false    kills .color-accent-from-page — the single highest-value
                             setting for zero-blue. CONFIRMED off.
    backgroundImage: ""      removes the chrome background image (bg_dark-8.png)

**Verified: the engine preserves hue.** From exactly-neutral seeds, every derived
variable came back exactly neutral (R=G=B) in both light and dark. Zero-blue survives
derivation — we do not need Vivaldi's hues to get a coherent ramp.

**Caveat found:** the derivation assumes headroom below `colorBg`. At trimfox's
`#202020` the bottom rung clipped to `#000000`; lifting the seed to `#2a2a2a` fixed it
(`--colorBgIntenser` → `#0f0f0f`) with no loss of neutrality.

**Also note:** `vivaldi.theme.schedule.enabled` defaults to `system`, and when it is
`system` the OS appearance **overrides `vivaldi.themes.current`**. Set the `o_s` map,
not just `current`, or the theme silently will not be the one you selected.

## Q4 — Light/dark switching `VERIFIED — and it resolves assumption A8`

`common.css` contains **zero** occurrences of `prefers-color-scheme`. Light and dark
are driven by Vivaldi's own theme classes:

    .theme-dark   .theme-light   .theme-schedule

**A8 is confirmed: trimfox's `@media (prefers-color-scheme: …)` approach will not
track Vivaldi's theme.** A user's Vivaldi theme (including its scheduled switching,
hence `.theme-schedule`) is independent of the OS appearance that
`prefers-color-scheme` reports.

**Consequence:** the palette's light/dark split must key off `.theme-dark` /
`.theme-light` rather than the media query. This is a small, contained change to the
one file that ports most cleanly (`grayscale.css`) — its *values* still port verbatim,
only the switching wrapper changes. It also pushes the Q3 decision toward
**cooperating with** Vivaldi's theme system rather than bypassing it.

## Q5 — Does `oklch()` work in Vivaldi's UI layer? `VERIFIED — yes`

Vivaldi's own UI CSS uses `oklch()` **zero** times, so its absence proved nothing
either way — it only told us Vivaldi does not rely on it.

**Tested directly in the UI context 2026-07-21, and it works:**

    CSS.supports('color', 'oklch(0.5 0.1 200)')   → true
    color: oklch(0.62 0.19 29)                    → computed value preserved
    color-mix(in oklch, red, blue)                → oklch(0.539974 0.285457 326.643)

So the privileged `chrome://` context behaves like ordinary page content here, and
trimfox's parametric `tinted` palette can port, not just `grayscale`.

## Q6 — Install / distribution and update survival `ANSWERED — observed, 2026-07-22`

> **Vivaldi auto-updated 8.1.4087.55 → 8.1.4087.56 mid-session, against a modded
> profile, unprompted.** So the thing we said could only be answered by waiting for a
> real update got answered by one. Measured immediately afterwards:
>
>     CSS mods still loading        ✅  00-selectors.css, 10-dials.css
>     our rules still applying      ✅
>     trimvaldi theme               ✅  theme-id-trimvaldi-dark
>     vertical tabs                 ✅  tabs-left
>     accentFromPage: false         ✅  still off
>     all 23 registered selectors   ✅  0 failures on the new build
>
> That last line is the useful one: the entire selector surface survived a real build
> change, checked by `tools/verify-selectors.py` ([ADR-0009](adr/0009-selector-registry-and-verifier.md)),
> which was written hours earlier and got an unplanned first real test.
>
> ⚠️ **Scope this claim honestly.** This was a **patch** update (`.55` → `.56`). It is
> strong evidence that mods and prefs survive routine updates — which is what the
> inference below predicted — but it is **not** evidence about a major version bump,
> where Vivaldi's UI DOM could change substantially. The README should say "survives
> routine updates, verified once" and not more.
>
> The original inference, now supported: the mods folder and the profile both live
> outside the app bundle, so an application update has no reason to touch them.

The CSS mods folder is user-chosen and lives outside the app bundle, which suggests
mods are **not** clobbered by application updates the way a patched `browser.html`
would be. Unconfirmed.

Vivaldi's settings live in a profile `Preferences` JSON that the application owns and
rewrites on exit — the basis for
[ADR-0004](adr/0004-settings-recipe-with-levelset-tests.md). **Still OPEN:** the exact
profile path, the key names trimvaldi needs, and merge-versus-rewrite behaviour on
upgrade. All of it must be asserted by the levelset tests before any patch writes.

## Q7 — Can settings actually be applied? `RESOLVED — yes, entirely`

> **CLOSED 2026-07-21 by the spike. It was never a blocker; it was a type error.**
>
> `prefs_definitions.json` gives `vivaldi.tabs.bar.position` as:
>
>     {"type":"enum","enum_values":{"top":0,"left":1,"right":2,"bottom":3},"default":"top"}
>
> **Enum prefs are stored as INTEGERS.** The failed attempt wrote the *string*
> `"left"`. The JSON pref store accepted it — which is exactly why it looked like
> "stored but ignored" — and the enum reader then discarded it as malformed and fell
> back to `top`. Writing **`1`** works immediately and completely:
> `#browser.tabs-left`, `#tabs-tabbar-container.left.wide`.
>
> **The whole trimvaldi setup is now scripted end to end with ZERO manual GUI steps**,
> verified live via `tools/cdp.py` plus two negative controls. See
> [`../spike/setup.sh`](../spike/setup.sh) and [`../spike/README.md`](../spike/README.md).
>
> **Transferable lesson: check a pref's TYPE in `prefs_definitions.json` before
> writing it.** None of the guesses below were the problem.
>
> The historical analysis is kept below because the *method* (grep the bundle, diff
> Preferences, distrust a value that persists but has no effect) was sound, and
> because it records how a plausible-but-wrong conclusion nearly killed ADR-0004.

Two mechanisms tried on 2026-07-21 against 8.1.4087.55; **neither works yet**.

**The `vivaldi.prefs` extension API is access-restricted.** It exists in the UI
context (`get`, `set`, `onChanged`, `resetAllToDefault`), but most paths return
*"The pref api is not allowed to access vivaldi.tabs.bar.position"*. Some are
readable (`vivaldi.homepage`, `vivaldi.tabs.new_page.custom_url`). Not a general
solution.

**Hand-patching `Preferences` JSON stored the value but had no effect.** With Vivaldi
fully quit, `vivaldi.tabs.bar.position = "left"` was written, Vivaldi relaunched, and:

- the value **persisted** in the file afterwards (not reverted),
- the profile has **no `protection` MAC block**, so it is not signature rejection,
- `"left"` is a **valid value** (the bundle uses `top`/`left`/`right`/`bottom`),
- but `#browser` still rendered `.tabs-top`.

So the pref is stored and ignored. Candidate explanations, untested: a
registered-pref **type** mismatch; per-**window** state overriding the global pref;
or a workspace/session layer taking precedence.

**Note on method:** authoritative pref *names* are greppable from the UI bundle —
`grep -rhoE '"vivaldi\.[a-z_.]+"' Resources/vivaldi/*.js`. That is how
`vivaldi.tabs.bar.position` was found after `bar_position` (an invented guess) failed.
Also note **default-valued prefs are absent from `Preferences` entirely** — they
appear only once changed, so a levelset test cannot simply assert "key exists"; it
must treat absent as default.

### Q7 UPDATE (2026-07-21, web research) — the mechanism is NOT broken

**Editing `Preferences` JSON demonstrably works.** Two independent projects do it:

- **[vivaldi-peek](https://github.com/xpltdco/vivaldi-peek)** — auto-collapsing vertical
  tabs, one-command install. Its installer **fully scripts the CSS-mod setup with no GUI
  steps**: backs up Preferences, sets `vivaldi.features.css_mods = true`, and sets
  `vivaldi.appearance.css_ui_mods_directory` to its CSS folder.
- **[vivaldi-customizations](https://github.com/kurtlieber/vivaldi-customizations)** — a
  `jq`-based script syncing toolbar/panel prefs under the `.vivaldi` key between profiles.

Both stress the same constraint we already found: **Vivaldi must be closed**, or it
overwrites the edit.

So the failure was specific to `vivaldi.tabs.bar.position`, not to the approach.
Suggestively, **vivaldi-peek does not script tab-bar position either** — it tells users
to set vertical tabs manually first. That hints this particular pref is governed by
something else (per-window state, or a companion key).

**Verified against 8.1.4087.55 locally:**

    vivaldi.appearance.css_ui_mods_directory   ✅ present in the UI bundle
    vivaldi.features.css_mods                  ❓ NOT in the UI bundle — likely a
                                                  browser-side flag; confirm by toggling
                                                  the experiment and diffing Preferences

**Revised read: [ADR-0004](adr/0004-settings-recipe-with-levelset-tests.md) is
plausible after all** — the patch half has working precedent. The open question shrinks
from "can settings be applied?" to "which specific prefs resist it?"

## Q8 — Is the trimfox look achievable in Vivaldi at all? `VERIFIED — yes, well-trodden`

The signature interaction — a collapsed vertical tab strip that expands on hover — is a
**common, solved Vivaldi mod** with multiple independent implementations:
[vivaldi-peek](https://github.com/xpltdco/vivaldi-peek),
[Achyuth072/Vivaldi-CSS](https://github.com/Achyuth072/Vivaldi-CSS), and a
[long-running forum thread](https://forum.vivaldi.net/topic/82900/vertical-tabs-collapsed-expand-on-hover).

Community selector pattern:

    #tabs-tabbar-container:is(.left, .right):not(:has(#tabs-subcontainer)):not(:hover)

This confirms `.left`/`.right` as the vertical state classes on `#tabs-tabbar-container`
(we observed `.top`), and `#tabs-tabbar-container` appears 288× in `common.css`.

**Update survival (Q6) effectively answered:** these mods live in the Vivaldi *User Data*
directory, never the application folder, so Vivaldi updates do not touch them.

**GUI enablement path** (if not scripted): `vivaldi://experiments` → "Allow for using CSS
modifications", then Settings → Appearance → Custom UI Modifications → select folder,
then restart.
