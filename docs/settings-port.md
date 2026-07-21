# Porting trimfox's `user.js` settings to Vivaldi

Charles asked whether the generic Firefox settings — blank start page and the like —
can come across. **Mostly yes, in intent.** This maps trimfox's `user.js` onto
Vivaldi's pref namespace.

Pref paths marked ✅ were read out of Vivaldi 8.1.4087.55's own UI bundle
(authoritative names) or confirmed live. Ones marked ❓ still need locating.

> **Blocked on a mechanism problem.** See the warning at the bottom — we do not yet
> have a working way to *apply* these. The mapping is still worth having; applying it
> is [ADR-0004](adr/0004-settings-recipe-with-levelset-tests.md)'s open problem.

## Three categories

trimfox's `user.js` splits cleanly:

1. **Firefox-only plumbing — does not port at all.**
   `toolkit.legacyUserProfileCustomizations.stylesheets`, `sidebar.revamp`,
   `sidebar.verticalTabs`, `widget.macos.native-context-menus`,
   `extensions.activeThemeID`. These solve Firefox-specific problems
   (enabling userChrome, forcing XUL menus) that do not exist in Vivaldi.
2. **Generic browser behaviour — ports in intent.** The table below.
3. **Chrome trimming** — in Vivaldi much of this is a native setting rather than CSS,
   which is the whole reason ADR-0004 exists.

## Start page / new tab — the thing you asked about

| trimfox intent | Firefox pref | Vivaldi pref |
|---|---|---|
| Blank homepage | `browser.startup.homepage` | `vivaldi.homepage` ✅ — currently `chrome://vivaldi-webui/startpage`; set to `about:blank` |
| Blank new tab (no Speed Dial) | `browser.newtabpage.enabled=false` | `vivaldi.tabs.new_page.custom_url` ✅ (empty by default) + its "new page choice" pref ❓ |
| Restore previous session | `browser.startup.page=3` | ❓ Vivaldi startup-behaviour pref |
| No new-tab content feeds | `browser.newtabpage.activity-stream.*` | Vivaldi's Speed Dial equivalents under `vivaldi.startpage.*` ✅ (e.g. `speed_dial.columns`, `background.*`, `navigation`) |

Vivaldi's Speed Dial is the analogue of Firefox's activity-stream new tab, and
`vivaldi.startpage.*` is a rich namespace — plenty of surface to blank it out.

## Chrome trimming

| trimfox intent | Vivaldi equivalent |
|---|---|
| No bookmarks toolbar (`browser.toolbars.bookmarks.visibility="never"`) | ✅ state class `.bookmark-bar-top-off` on `#browser`; pref under `vivaldi.bookmarks.*` ❓ |
| Compact density (`browser.uidensity=1`) | ✅ state class `.density-on`; pref ❓ |
| Vertical tab strip (`sidebar.verticalTabs`) | ✅ `vivaldi.tabs.bar.position` — values `top`/`left`/`right`/`bottom` |
| Status bar — trimfox has none to hide | Vivaldi adds one: `#footer .toolbar-statusbar`. Native setting ❓ |
| No tab hover previews (`browser.tabs.hoverPreview.enabled=false`) | ❓ likely under `vivaldi.tabs.*` |
| Closing last tab keeps window (`browser.tabs.closeWindowWithLastTab=false`) | ❓ |

## URL bar noise

trimfox switches off nine `browser.urlbar.suggest.*` prefs. Vivaldi's analogue is the
`vivaldi.address_bar.*` namespace ✅, which is at least as granular — confirmed
members include `autocomplete.enabled`, `inline_search.enabled`,
`inline_search.suggest_enabled`, `omnibox.bookmarks_boosted`,
`highlight_base_domain`, `extensions.visible`.

Same intent, different names: strip predictive/suggestion clutter from the dropdown.

## Things Vivaldi needs that Firefox never did

Not a port — new decisions, because Vivaldi ships UI Firefox has no equivalent of:

- **Panels rail** (`#main.left`) — trimfox has no analogue. Trim or keep?
- **Workspaces button** in the tab bar (`.tabbar-workspace-button`).
- **`.color-accent-from-page`** — Vivaldi tints its chrome from the page's theme
  colour. This is **directly hostile to the zero-blue grayscale ethos** and should
  almost certainly be switched off. Highest-value single setting for the look.
- **Tab stacking** — trimfox never had it.

## ⚠️ Mechanism is unresolved — do not assume this can be applied yet

Two blockers found on 2026-07-21:

1. **The `vivaldi.prefs` extension API is access-restricted.** It exists in the UI
   context with `get`/`set`, but most paths return *"The pref api is not allowed to
   access vivaldi.tabs.bar.position"*. Only some prefs (e.g. `vivaldi.homepage`) are
   readable. So driving settings through the UI's own API is not a general solution.
2. **Hand-patching `Preferences` JSON did not take effect.** With Vivaldi fully quit,
   setting `vivaldi.tabs.bar.position = "left"` persisted in the file across a
   relaunch (verified still present afterwards, and the profile has no `protection`
   MAC block) — **but the UI still rendered `tabs-top`.** So the value is being
   stored and ignored, meaning something else governs it: possibly a registered-pref
   type mismatch, a per-window state store, or a separate workspace/session layer.

**Consequence for ADR-0004:** its premise — "scripted `Preferences` patch gated by
levelset tests" — is not yet demonstrated to work at all. The levelset tests would
have caught this, which is the good news; but the patch mechanism itself needs a
working proof before the ADR can be relied on. Recorded as research Q7.
