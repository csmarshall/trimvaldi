# Vivaldi UI DOM map

**Mapped against Vivaldi 8.1.4087.55** (arm64 macOS) on 2026-07-21, live via the
DevTools Protocol against a throwaway profile.

## How to reproduce

Vivaldi's UI is a web page, so it can be driven programmatically — no clicking:

```sh
./tools/dev-browser.sh              # launch with DevTools on :9222, disposable .dev-profile/
./tools/cdp.py window.html <<'JS'
document.querySelector('#browser').className
JS
./tools/dev-browser.sh --stop       # quit when done
```

`--fresh` wipes the profile first, for a clean-slate map. `tools/cdp.py` connects to
the first DevTools target matching a URL substring and evaluates JS in it. The UI
target is `chrome-extension://mpognobbkildjkofajifpdfhcoklimli/window.html`
(`main.html` is a second app target).

Requires Python `websockets` (`python3 -c 'import websockets'` to check).

**Never hand-patch `Preferences` while Vivaldi is running** — it owns that file and
rewrites it on exit, silently clobbering the edit. `dev-browser.sh --stop` first.

## The skeleton

```
body
  #app
    #browser.mac.theme-dark…              ← ALL global state lives here
      #header
        .tabbar-wrapper
          #tabs-tabbar-container.top
            #tabs-container.top
              .window-buttongroup          ← macOS traffic lights
              .toolbar.toolbar-tabbar-before
                .tabbar-workspace-button
              .resize
                .tab-strip                 ← the tabs
              .toolbar.toolbar-tabbar-after
                .button-toolbar.newtab     ← new-tab button (trim target)
                .button-toolbar.toolbar-spacer-flexible
                .button-toolbar.tabs-button
      #main.left
        .mainbar                           ← address bar row
        .inner                             ← page content
      #footer
        .toolbar.toolbar-statusbar         ← status bar (trim target)
```

## `#browser` — the state-class surface

**This is the single most important element in the UI.** Every global piece of state
is a class on `#browser`, which makes it the styling hook for essentially everything:

```
mac  normal  theme-id-Vivaldi2  theme-dark  bg-dark
unified-ui  unified-ui-transparent  color-accent-from-page
auto-hide-off  disable-titlebar  isblurred  density-on  dim-blurred
alt-tabs  substrip-tabs-on  full-key-access  stacks-substrip
address-top  mail-bar-top  bookmark-bar-top-off  tabs-top  macos26
```

Read off that list:

| Class | Meaning |
|---|---|
| `.theme-dark` / `.theme-light` | **the light/dark switch** — see below |
| `.mac`, `.macos26` | platform / OS version |
| `.tabs-top` | tab bar position (`tabs-left` etc. when moved) |
| `.address-top` | address bar position |
| `.bookmark-bar-top-off` | bookmark bar hidden |
| `.density-on` | compact density |
| `.isblurred` | **window focus state** — the trimfox `--tf-*-inactive` tokens map here |
| `.disable-titlebar` | native titlebar off |
| `.color-accent-from-page` | accent derived from page — likely a trim target |

`.isblurred` deserves emphasis: trimfox has a whole inactive-window token set
(`--tf-line-inactive`, `--tf-highlight-inactive`) that in Firefox required
`:-moz-window-inactive`. Here it is a plain class on a known element — **easier than
Firefox.**

## Light/dark — confirms assumption A8

`.theme-dark` / `.theme-light` are on `#browser`, **not** `html` or `body`, and
`common.css` uses `prefers-color-scheme` zero times. So the palette must be scoped:

```css
#browser.theme-dark  { --tf-surface: #202020; … }
#browser.theme-light { --tf-surface: #ececec; … }
```

The trimfox palette **values** port verbatim; only the wrapper changes from
`@media (prefers-color-scheme: …)` to these classes. There is also `.theme-schedule`
for Vivaldi's scheduled switching, and `.theme-id-Vivaldi2` naming the active theme.

## Tab strip

```
.tab-strip
  span
    .tab-position
      #tab-694168866.tab-wrapper.active.uifocusstop.extended
        .tab.active.periodic-reload
          .tab-header
```

Stable hooks: `.tab-strip`, `.tab-position`, `.tab-wrapper`, `.tab`, `.tab-header`,
plus state classes `.active`. Measured `.tab-strip` box in horizontal mode:
`180x30 @ 215,6`.

## Address bar

```
.mainbar
  .toolbar.toolbar-mainbar.toolbar-addressbar.toolbar-visible.toolbar-large
    .button-toolbar × N            ← nav buttons, each wrapping .ToolbarButton-Button
    .UrlBar-AddressField.urlfield-anchor
      .toolbar.toolbar-insideinput
        .button-addressfield.SiteInfoButton
      .UrlBar-UrlFieldWrapper
      .toolbar.toolbar-insideinput
        .BookmarkButton
    .toolbar-extensions
```

## ⚠️ Selector stability — read before writing any CSS

Feeds directly into [ADR-0002](adr/0002-centralize-selectors.md).

1. **NEVER target UUID classes.** Many toolbar buttons carry a per-instance UUID
   class, e.g.
   `.button-toolbar.workspace-popup.tabbar-workspace-button.aed38994-2044-468e-b808-06abf04c698b`.
   **These change between profiles and between launches** — confirmed: the same
   button had `afdfefec-…`, then `c3c37c2b-…`, then `aed38994-…` across three
   launches of the same build. They are instance identity, not semantics.
1b. **UUIDs also appear as `id`s, not only classes** (found 2026-07-22):
   `div#b32f739c-3a5e-4c4c-b261-89b431e353f3.button-toolbar.toolbar-spacer-panel`.
   Same rule applies — never target them.
1c. **IDs ARE NOT UNIQUE in Vivaldi's UI** (found 2026-07-22). `#ui-region-panel_button`
   exists **10 times** in one window. An `#id` selector can silently match a crowd,
   and `document.querySelector('#…')` silently returns only the first — so DOM
   exploration can under-report. Check `querySelectorAll(...).length`.
2. **NEVER target `#tab-<id>`.** Per-tab runtime ids (`#tab-694168866`).
3. **Prefer** `#browser` state classes, semantic component classes
   (`.tab-strip`, `.UrlBar-AddressField`, `.toolbar-statusbar`), and structural
   containers (`#header`, `#main`, `#footer`).
4. Vivaldi's names bear **zero** resemblance to Firefox's — confirming ADR-0001's
   premise rather than assuming it.

## Static recon shortcut

Vivaldi ships its UI unpacked, so selectors can be found without devtools:

```
/Applications/Vivaldi.app/Contents/Frameworks/Vivaldi Framework.framework/
  Versions/<version>/Resources/vivaldi/     ← version dir changes on every update
    window.html          entry point
    style/common.css     1023K — the whole UI theme
    *.js                 the UI bundle (greppable for pref path names)
```

Use the live DOM to confirm what is *actually rendered*; use the files to discover
what exists.

## `#main > .inner` — where the strip actually lives (mapped 2026-07-22)

Vertical tab mode, once `vivaldi.tabs.bar.position = 1`:

```
#main.left
  .mainbar                          [1440x54]   address bar, full width
  .inner
    #modal-bg
    #panels-container.left.icons    [41x1584]   ← the PANEL RAIL
    .tabbar-wrapper                 [14x1584]   ← the tab strip (collapsed)
    #webview-container              [1385x1584]
```

**The panel rail is a DOM sibling BEFORE the tab strip**, which is why the strip is
not the leftmost element. Trimming the rail is a pref
(`vivaldi.panels.state` / `window_defaults` → `barVisible: false`), and doing so makes
the strip leftmost with no CSS reordering.

### ⚠️ Fixed insets dominate at rail width

Vivaldi styles vertical tab strips with:

```
#tabs-container.left .tab-strip {
  margin: 0 max(calc(var(--densityGap) * 2), 1px);
  max-width: calc(100% - var(--densityGap) * 2);
}
```

That is 6px each side. At the native 360px it is imperceptible. **At a 14px collapsed
rail it consumes 12 of 14**, leaving `.tab-position` 2px wide — the per-tab separator
lines still render, but at 2px they are invisible and the rail reads as empty chrome
with no hint a tab bar exists.

Vivaldi's own fix for maximized/fullscreen vertical tabs is
`margin: 0; max-width: 100%`, so overriding it follows the grain rather than fighting.

**Generalize this:** a collapsed rail is not merely a narrow sidebar. Any fixed padding,
margin, gap or min-width that is invisible at full width may dominate at 14px.

## Still unmapped

- Panels rail internals, menus, tab stacks, pinned tabs
- Panels rail, menus, tab stacks, pinned tabs
- The `.inner` / page-content boundary the overlay strip
  ([ADR-0005](adr/0005-hover-expand-overlays.md)) must float above
