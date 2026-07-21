# ADR-0004 — Ship a scripted settings patch, gated by levelset tests

- **Status:** Accepted
- **Date:** 2026-07-21
- **Ancestor:** trimfox `user.js` / `install.sh`; [ADR-0007 — trimfox-drift](https://github.com/csmarshall/trimfox/blob/main/docs/adr/0007-trimfox-drift-monitor.md)

## Context

A large share of trimvaldi's trimming is not CSS at all. Vivaldi ships denser default
chrome than Firefox (status bar, panel rail, extra address-bar controls) but is also
far more configurable, so much of the trim is a *setting* rather than a rule. Without
those settings applied, the theme does not look right out of the box.

trimfox solves the equivalent problem elegantly: `user.js` is a supported drop-in
file, and `install.sh` places it. Vivaldi has no such thing. Its settings live in a
**`Preferences` JSON file inside the profile that the application itself owns and
rewrites.**

That makes the obvious options both unattractive. Documented manual steps are safe
but tedious and drift out of date silently. A blind scripted patch is convenient but
writes into a file we do not own, against key names we have not verified, on a
version we may not have tested.

The failure mode that actually matters is not "the patch does not apply" — it is
"the patch applies to the wrong key on a newer Vivaldi and corrupts someone's
profile."

## Decision

**Ship the scripted patch, but gate it behind levelset tests that validate our
assumptions against the Vivaldi actually installed.**

The script never writes until a pre-flight pass succeeds:

1. **Detect** the installed Vivaldi version and record it in the run output.
2. **Assert** every `Preferences` key trimvaldi intends to touch exists and has the
   expected type/shape. A missing or retyped key is a hard stop, not a warning.
3. **Refuse to run while Vivaldi is open.** Chromium-family browsers hold preferences
   in memory and rewrite the file on exit, so patching a running browser is silently
   clobbered. This is a correctness requirement, not politeness.
4. **Back up** `Preferences` before writing.
5. **Patch** only the asserted keys; never wholesale-rewrite the file.
6. **Report** the version tested against, so a user on a newer build knows their
   result is unverified rather than assuming it was blessed.

The same assertions run in CI against current stable Vivaldi, so the project learns
that Vivaldi moved a setting **before a user does** — the `trimfox-drift` pattern
applied to the settings layer instead of the chrome layer.

## Consequences

- **Positive:** one-command setup close to trimfox's `install.sh` ergonomics, without
  the recklessness of patching an application-owned file on unverified assumptions.
- **Positive:** the assertion list doubles as documentation of exactly which settings
  trimvaldi depends on — enumerable, auditable, and monitorable, in the same spirit as
  [ADR-0002](0002-centralize-selectors.md).
- **Positive:** failures are loud and pre-emptive; the script's default posture is to
  refuse rather than to guess.
- **Trade-off:** meaningfully more work than documented steps, and the test harness is
  a maintained artifact in its own right. Accepted deliberately: this is the "build
  the harness" half of trimfox's founding ethos, not gold-plating.
- **Trade-off:** a levelset pass proves the keys exist on the tested version — it does
  not prove the resulting *look* is right. Visual verification stays manual.
- **Open:** exact profile path, key names, and whether Vivaldi rewrites or merges the
  file on upgrade. All unverified — see [`../vivaldi-research.md`](../vivaldi-research.md)
  Q1 and Q6. Nothing here is implementable until Vivaldi is installed.
