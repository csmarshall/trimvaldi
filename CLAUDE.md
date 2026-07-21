# trimvaldi — repo context

Permanent, repo-specific context. Committed. Global preferences live in
`~/.claude/CLAUDE.md`; transient state lives in `session-state.md` (gitignored).

## What this is

A Vivaldi browser UI theme that carries over the **design language** of
[trimfox](https://github.com/csmarshall/trimfox) (`~/work/trimfox`) — Charles's
macOS Firefox `userChrome` theme.

trimfox in one line: trim everything that isn't a tab. Grayscale, zero-blue, a
skinny tab strip that expands on hover, minimal chrome, no extensions.

## The single most important constraint

**Vivaldi has no `userChrome.css`. None of trimfox's CSS transfers.**

Firefox chrome is XUL styled through `userChrome.css`. Vivaldi is Chromium-based
and its UI is an ordinary web app (`browser.html`) rendered in a Chromium view —
so it is styled with ordinary web CSS against ordinary DOM. Both are "CSS", and
that is where the similarity stops: **zero shared selectors, zero shared chrome
variables, zero shared file mechanics.**

So this is a ground-up reimplementation that inherits:

- the **design language** — grayscale / zero-blue, extreme trim, hover-expand strip
- the **token architecture** — `--tf-*` custom properties, dial defaults separated
  from palettes, a user-overrides layer that wins by source order (no `!important`)
- the **philosophy** — customize without forking; `git pull` never conflicts

It inherits **no CSS rules**. Do not copy selectors from trimfox and expect them
to resolve. Port intent, not code.

## What Vivaldi already gives us for free

Relevant because it changes what's worth building. Vivaldi ships **native vertical
tabs** (tab bar left/right) and **tab stacking** as first-class features. A large
part of trimfox's headline work — coaxing Firefox into a usable vertical strip —
is simply not needed here. The interesting work in trimvaldi is the *trimming*,
the *palette*, and the *hover-expand behaviour*, not the tab strip's existence.

**More than expected is a pref rather than a rule** — and this is the biggest
correction the spike made to the plan. Vivaldi's theme engine computes ~117
`--color*` properties and writes them as an inline style on `#browser`, so CSS
cannot recolour the chrome without `!important` on every one. But those 117 derive
from a theme object of ~5 seed colours, and themes are ordinary prefs. So:

- **The palette ships as a native Vivaldi theme, not a stylesheet**
  ([ADR-0007](docs/adr/0007-palette-is-a-native-theme.md)). CSS keeps structure,
  layout, trimming and the `--tf-*` vocabulary used by our own rules.
- Much of the *trim* is also a pref, not CSS — status bar, panel rail, and the
  page-derived accent that is most hostile to zero-blue.

So the deliverable is **not** the `user.js` + `userChrome.css` shape that
`docs/design-ethos.md` A2/A3 predicted. Expect *palette definition + generator +
a much smaller stylesheet*, with the settings recipe carrying more of the load.

## Status

**Feasibility proven; the real theme is not built yet.** Vivaldi **8.1.4087.55** is
installed on `toad` (brew cask). `css/` is still empty — what exists is a throwaway
feasibility spike in `spike/`, plus verified research.

What the spike established (see [`spike/README.md`](spike/README.md)):

- **A full install needs ZERO manual GUI steps.** Measured, with negative controls.
  Everything is a pref write to a closed profile.
- **`docs/vivaldi-research.md` Q1, Q3, Q5, Q7 are CLOSED** by measurement.
  **Q6 (update survival) is still genuinely OPEN** — inference only, never observed.
  Do not state it as fact.
- The signature collapsed/hover-expand strip works and overlays without reflow.

Items still marked `OPEN` in `docs/vivaldi-research.md` remain unverified — do not
present them as fact. Items now marked `VERIFIED` were measured against this exact
build and may not hold for others.

### Two things that will bite you

1. **Read `prefs_definitions.json` before writing ANY pref.** It ships in the Vivaldi
   bundle and is an authoritative registry of 618 prefs *with types and defaults*.
   **`enum` prefs are stored as INTEGERS** — writing the string label persists
   silently and is then ignored. That one mistake looked like a hard blocker for a
   whole session. Default-valued prefs are **absent** from `Preferences` entirely, so
   absent means default, not missing.
2. **Never patch `Preferences` while Vivaldi is running** — it owns the file and
   rewrites it on exit, silently clobbering the edit. Stop it first.

## Layout

    css/      the Vivaldi custom-UI stylesheets (the theme itself) — still empty
    docs/     migration brief, research/verification log, ADRs as they accrue
    spike/    THROWAWAY feasibility proof. Not the theme; expected to be deleted
              once its findings are absorbed. Read spike/README.md before touching
              anything here — it holds the measurements the ADRs rest on.
    tools/    dev-browser.sh (Vivaldi + DevTools on :9222, disposable .dev-profile/)
              and cdp.py (evaluate JS in the UI context). The UI is a web page, so
              it is fully scriptable — map and verify programmatically, never by eye.

## Conventions carried over from trimfox

- Conventional commits (`fix:` / `feat:` / `docs:` / `chore:`) — enables
  release-please later if this repo grows to need releases.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Design tokens are `--tf-*` (shared vocabulary with trimfox, deliberately — the
  two themes should feel like one family and a palette should be legible in both).
- MIT, © 2026 Charles Marshall.
