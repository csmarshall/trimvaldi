# Vivaldi research — verification log

**Everything on this page is UNVERIFIED until checked against a real install.**

Vivaldi is not installed on `toad` as of 2026-07-21, so none of the below has been
confirmed on this machine. It is recollection and needs checking. Treat each item
as a question to answer, not a fact to cite — and do not repeat any of it to
Charles as settled.

Mark items `VERIFIED <date>` with the evidence as they are confirmed.

## Q1 — How are custom UI CSS mods enabled? `UNVERIFIED`

Recollection: Vivaldi's UI is `browser.html` rendered in a Chromium view. Two
approaches have existed over time:

- **Historic / manual:** hand-edit `browser.html` inside the application bundle to
  `<link>` a custom stylesheet. Survives poorly — an app update overwrites it.
- **Supported setting:** newer Vivaldi versions expose a "custom UI modifications"
  folder in Settings → Appearance, pointed at a directory of `.css` files, with a
  matching toggle under `vivaldi://experiments`.

**To confirm:** which mechanism the current Vivaldi build uses, the exact settings
path, the exact flag name, whether it survives updates, and whether a restart is
needed per change (trimfox's edit-and-restart loop may or may not apply).

## Q2 — What does the tab bar DOM actually look like? `UNVERIFIED`

Recollection of Vivaldi-ish selectors: `#browser`, `#tabs-container`,
`.tabbar-wrapper`, `.tab-position`, `.tab`, `#header`, `.toolbar`, `#addressfield`,
`.panel`. **Low confidence — verify every one.**

**To confirm:** the real element tree for the tab bar in vertical mode, collapsed
vs expanded, plus pinned tabs and tab stacks.

**How:** Vivaldi's own UI is inspectable with devtools once enabled (the UI is a
web page). That inspection replaces trimfox's "read Firefox's chrome CSS" step and
is the single highest-value first action after install.

## Q3 — What theme variables does Vivaldi expose? `UNVERIFIED`

Recollection: a theme engine with custom properties along the lines of
`--colorBg`, `--colorFg`, `--colorAccentBg`, `--colorHighlightBg`, `--colorBorder`.
Names and completeness both unconfirmed.

**To confirm:** the real variable set, whether it covers everything trimvaldi needs
to recolour, and how it reacts to light/dark and to user-selected themes. Drives
the "drive vs bypass the theme engine" decision in the migration brief.

## Q4 — Native vertical tabs and hover-expand `UNVERIFIED (feature exists; behaviour unconfirmed)`

Vivaldi ships vertical tabs (tab bar left/right) and tab stacking — this much is
well established. What is unconfirmed is whether it offers a **collapse /
expand-on-hover** strip like the one trimfox builds, natively or via a setting.

**To confirm:** if native, trimvaldi styles it and phase 4 shrinks to almost
nothing. If not, we build hover-expand in CSS (Chromium CSS makes this more
tractable than it was in Firefox).

## Q5 — Does `oklch()` work in Vivaldi's UI layer? `UNVERIFIED (very likely yes)`

Chromium has supported `oklch()` since 111, and Vivaldi tracks Chromium closely,
so the parametric palette should carry over. Confirm anyway — the UI layer can lag
or restrict what page content gets.

## Q6 — Install / distribution story `UNVERIFIED`

trimfox ships `install.sh` + a release zip that drops files into a Firefox profile.
The Vivaldi equivalent depends entirely on Q1.

**To confirm:** where the CSS folder lives per-user, whether it is profile-scoped,
and what a one-command install would look like. Also whether mods survive Vivaldi
updates — if they do not, that is a prominent README warning, the way trimfox warns
about Firefox updates.
