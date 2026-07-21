# Vivaldi research — verification log

**Reference build:** Vivaldi **8.1.4087.55** (arm64 macOS), installed via
`brew install --cask vivaldi` on 2026-07-21 on `toad`.

Items are marked `VERIFIED` with evidence, or `OPEN` where still unconfirmed. Do not
cite an `OPEN` item as fact.

## The single most useful discovery

**Vivaldi ships its entire UI unpacked and readable on disk.** No archive to extract,
no devtools required for static recon:

    /Applications/Vivaldi.app/Contents/Frameworks/Vivaldi Framework.framework/
      Versions/8.1.4087.55/Resources/vivaldi/
        window.html          the UI entry point
        style/common.css     1023K — the entire UI theme
        components/          per-feature CSS

This is a materially better position than trimfox had with Firefox, where chrome CSS
lives inside `omni.ja` and had to be unzipped to inspect. Here the whole dependency
surface is greppable directly. Devtools remain necessary for *live DOM* confirmation
(the CSS may contain legacy or unused selectors), but selector discovery is now a
`grep`.

## Q1 — How are custom UI CSS mods injected? `VERIFIED (mechanism) / OPEN (folder)`

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

**Still OPEN:** where the css-mods folder lives on disk, the settings path that points
Vivaldi at it, and — important for ADR-0006 — whether the endpoint concatenates
multiple files and in what order. If order within the folder is not controllable, the
single-entry-file-plus-`@import` plan is what saves us; confirm `@import` resolves from
that `chrome://` endpoint.

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

## Q3 — Vivaldi's theme variables `VERIFIED (they exist) / OPEN (coverage)`

A substantial custom-property theme system, e.g.:

    --colorBg          --colorFg          --colorAccentBg     --colorAccentFg
    --colorBgDark      --colorBgAlpha     --colorAccentBgFaded  --colorAccentBorder
    (plus Alpha / Faded / Dark / Darker / Heavy variants throughout)

**Still OPEN:** whether these cover everything trimvaldi needs to recolour, and
therefore whether we drive Vivaldi's theme engine or bypass it. That decision remains
open, but Q4 below now pushes it.

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

## Q5 — Does `oklch()` work in Vivaldi's UI layer? `OPEN (likely yes)`

Vivaldi's own UI CSS uses `oklch()` **zero** times, so its absence proves nothing
either way — it only tells us Vivaldi does not rely on it. Chromium has supported
`oklch()` since 111 and Vivaldi 8.1 tracks a far newer Chromium, so the parametric
`tinted` palette should carry over. **Confirm by testing in the UI layer specifically**
before depending on it; the UI is a privileged `chrome://` context and need not behave
identically to page content.

## Q6 — Install / distribution and update survival `OPEN`

The CSS mods folder is user-chosen and lives outside the app bundle, which suggests
mods are **not** clobbered by application updates the way a patched `browser.html`
would be. Unconfirmed.

Vivaldi's settings live in a profile `Preferences` JSON that the application owns and
rewrites on exit — the basis for
[ADR-0004](adr/0004-settings-recipe-with-levelset-tests.md). **Still OPEN:** the exact
profile path, the key names trimvaldi needs, and merge-versus-rewrite behaviour on
upgrade. All of it must be asserted by the levelset tests before any patch writes.

## Q7 — Can settings actually be applied? `OPEN — BLOCKER for ADR-0004`

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
