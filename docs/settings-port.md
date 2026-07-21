# Porting trimfox's `user.js` settings to Vivaldi

Charles asked whether the generic Firefox settings — blank start page and the like —
can come across. **Mostly yes, in intent.** This maps trimfox's `user.js` onto
Vivaldi's pref namespace.

Pref paths marked ✅ were read out of Vivaldi 8.1.4087.55's own UI bundle
(authoritative names) or confirmed live. Ones marked ❓ still need locating.

> **✅ UNBLOCKED 2026-07-21.** The earlier "we have no working way to apply these"
> warning was **wrong** and has been replaced at the bottom of this file. Prefs are
> fully scriptable; the failure was a single type error. See
> [`vivaldi-research.md`](vivaldi-research.md) Q7 and [`../spike/`](../spike/).

## Read `prefs_definitions.json` before writing ANY pref

    Resources/vivaldi/prefs_definitions.json

618 prefs with **names, types and defaults** — authoritative, straight from the build.
Use it instead of guessing, and instead of grepping the JS bundle for names alone.

**Types matter more than names.** `enum` prefs are stored as **integers**, not their
string labels — writing the label persists silently and is then ignored, which cost a
whole session. And **default-valued prefs are absent from `Preferences` entirely**, so
a levelset test must treat *absent* as *default*, never as *missing*.

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
| Vertical tab strip (`sidebar.verticalTabs`) | ✅ `vivaldi.tabs.bar.position` — **enum, write the INT**: `top`0 `left`1 `right`2 `bottom`3 |
| Status bar — trimfox has none to hide | ✅ `vivaldi.status_bar.display` — enum `on`0 / `off`1 / `overlay`2. Write `1`. |
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

- **Panels rail** (`#main.left`) — trimfox has no analogue. **DECIDED: trim it.**
  Charles's reasoning, and it is the right test to apply: everything the rail exposes
  is reachable by keyboard shortcut or menu, so a permanently-visible column of icons
  is not earning its space for ~all interactions.

  **Crucially, the rail and the panels are separate flags**, so trimming the rail does
  *not* remove the capability — the trimfox move of deleting the persistent affordance
  while keeping the function:

      vivaldi.panels.state           {"barVisible": …, "panelVisible": …, "width": 34}
      vivaldi.panels.window_defaults same shape — the defaults for NEW windows.
                                     Set both, or new windows get the rail back.

  Related and worth taking while we are here: `vivaldi.panels.as_overlay.enabled`
  (bool, default `false`) makes panels overlay content instead of pushing it —
  natively, exactly the behaviour [ADR-0005](adr/0005-hover-expand-overlays.md)
  argues for on the tab strip.

  ⚠️ **One genuine exception to "it's all in a menu": web panels** — docked websites
  (`vivaldi.panels.web.items`), where the docked surface *is* the feature. They remain
  reachable via Quick Commands with the rail hidden, so this is a trim, not a removal;
  worth a line in the README's "Heads up" section rather than a silent deletion.
- **Workspaces button** in the tab bar (`.tabbar-workspace-button`).
- **`.color-accent-from-page`** — Vivaldi tints its chrome from the page's theme
  colour. This is **directly hostile to the zero-blue grayscale ethos** and should
  almost certainly be switched off. Highest-value single setting for the look.
- **Tab stacking** — trimfox never had it.

## ✅ Mechanism RESOLVED — patching `Preferences` works

Superseding the "mechanism is unresolved" warning that stood here until 2026-07-21.

**Hand-patching `Preferences` works.** The one failure — `vivaldi.tabs.bar.position`
persisting but being ignored — was a **type error, not a mechanism failure**: it is an
`enum`, stored as an **integer** (`left` = `1`), and the string `"left"` was written.
Of the three hypotheses recorded at the time (type mismatch / per-window state /
workspace layer), the first was correct.

The `vivaldi.prefs` extension API *is* still access-restricted, and that finding
stands — but it no longer matters, because we never needed it.

**Confirmed working recipe** (Vivaldi **must** be closed — it owns these files and
rewrites them on exit):

| Intent | Pref | Value |
|---|---|---|
| Register the CSS mods folder | `vivaldi.appearance.css_ui_mods_directory` | path string |
| Vertical tab strip | `vivaldi.tabs.bar.position` | `1` (int) |
| Palette / accent / radius | `vivaldi.themes.user` + `vivaldi.themes.current` | theme objects |
| Light↔dark mapping | `vivaldi.theme.schedule.o_s` | `{"light": id, "dark": id}` |

⚠️ `vivaldi.theme.schedule.enabled` defaults to `system`, and while it is `system` the
**OS appearance overrides `vivaldi.themes.current`**. Set the `o_s` map as well, or the
active theme silently will not be the one you selected.

**Consequence for ADR-0004:** its premise is **demonstrated**, not merely plausible.
The patch half is proven end to end with zero GUI steps; the levelset-test half is
still to be written, and `prefs_definitions.json` gives it its expected types and
defaults for free.
