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

## Status

Pre-implementation. Nothing is built. **Vivaldi is not yet installed on `toad`** —
that is step 0. Until it is, every Vivaldi specific in these docs (settings paths,
experiment flags, selector names, theme variable names) is **unverified** and
explicitly marked as such in `docs/vivaldi-research.md`. Verify before relying on
any of it; do not present unverified specifics as fact.

## Layout

    css/      the Vivaldi custom-UI stylesheets (the theme itself)
    docs/     migration brief, research/verification log, ADRs as they accrue

## Conventions carried over from trimfox

- Conventional commits (`fix:` / `feat:` / `docs:` / `chore:`) — enables
  release-please later if this repo grows to need releases.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Design tokens are `--tf-*` (shared vocabulary with trimfox, deliberately — the
  two themes should feel like one family and a palette should be legible in both).
- MIT, © 2026 Charles Marshall.
