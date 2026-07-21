# Architecture Decision Records

Decisions and the reasoning behind them, so they are recorded rather than
re-derived. Ordered by when the decision was made.

trimvaldi's ADRs start at **0001 in this repo** rather than continuing
[trimfox](https://github.com/csmarshall/trimfox)'s numbering — the reasoning is
inherited, but each decision is made fresh against a different browser. Every ADR
cites its trimfox ancestor where one exists.

| # | Decision | Ancestor |
|---|---|---|
| [0001](0001-ethos-faithful-port.md) | Ethos-faithful port, not a pixel-identical reproduction | trimfox ADR-0001 |
| [0002](0002-centralize-selectors.md) | Centralize every Vivaldi selector in one file | trimfox ADR-0005, 0007 |
| [0003](0003-cascade-layers-override.md) | Enforce the override contract with CSS cascade layers | trimfox ADR-0006 |
| [0004](0004-settings-recipe-with-levelset-tests.md) | Ship a scripted settings patch, gated by levelset tests | trimfox `user.js`, ADR-0007 |
| [0005](0005-hover-expand-overlays.md) | The hover-expanded tab strip overlays content rather than pushing it | trimfox ADR-0002 |

All five were taken on 2026-07-21, before any code existed, off the back of
[`../design-ethos.md`](../design-ethos.md). Their Vivaldi-specific premises are still
**unverified** pending an install — see [`../vivaldi-research.md`](../vivaldi-research.md).
