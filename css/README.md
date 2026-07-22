# css/

The Vivaldi custom-UI stylesheets. Load order is alphabetical — the css-mods
endpoint emits one `@import` per file, sorted — so the numeric prefixes **are**
the cascade order.

    00-selectors.css      the ONLY hand-written file naming Vivaldi's DOM or
                          variables. Rules + the machine-checked registry.
    10-dials.css          structural --tf-* defaults (sizes, motion). No colour.
    20-palette.css        GENERATED — do not edit. See below.
    99-user-overrides.css yours, gitignored, loaded LAST so it wins by plain
                          source order — no !important needed.

## Colour does not live here

This is the biggest departure from trimfox, and it is worth understanding before
looking for a palette file to edit.

Vivaldi computes ~117 `--color*` properties and writes them as an **inline style
on `#browser`**, which CSS cannot override without `!important` on every one. But
it *derives* all 117 from about **five seed colours** — so trimvaldi ships its
palette as a **native Vivaldi theme**, applied as a pref
([ADR-0007](../docs/adr/0007-palette-is-a-native-theme.md)).

One definition generates both halves
([ADR-0008](../docs/adr/0008-one-palette-definition.md)):

    palettes/grayscale.ini              ← the only place a colour is chosen
           ├──→ css/20-palette.css              (generated)
           └──→ palettes/grayscale.theme.json   (generated)

    tools/build-palette.py              regenerate
    tools/build-palette.py --check      fail if the outputs are stale

So a token can be in one of three places, and the generator **enforces** the split
so nothing is defined twice:

| Class | Where it lives | Examples |
|---|---|---|
| **Aliased** | `00-selectors.css`, from Vivaldi's own variable | `--tf-surface`, `--tf-text` |
| **Derived** | `00-selectors.css`, via `color-mix()` from trimfox's formula | `--tf-line-solid`, `--tf-highlight` |
| **Generated** | `20-palette.css`, from the `.ini` | `--tf-raised`, `--tf-text-dim`, `--tf-glyph` |

Aliased and derived tokens follow light/dark automatically, because Vivaldi swaps
the seeds and the derivation follows them.

## Overriding

**You never need `!important`, and you never need to run the generator.** Redefine
any `--tf-*` token in `99-user-overrides.css`; it loads last and wins on source
order ([ADR-0006](../docs/adr/0006-import-order-not-cascade-layers.md)).

The one thing an override cannot change is the **chrome palette itself** — that is
the Vivaldi theme, not CSS. Changing it means editing a palette definition and
re-running the generator, which is a different (documented) operation. This
distinction does not exist in trimfox and is the price of the chrome actually
being recolourable at all.

## Checking it still works

    ./tools/dev-browser.sh
    ./tools/verify-selectors.py

Every Vivaldi selector and variable we depend on is registered in
`00-selectors.css` and live-checked against a running browser
([ADR-0009](../docs/adr/0009-selector-registry-and-verifier.md)). A renamed
Vivaldi class does not error — it silently stops applying — so this is the only
thing standing between us and a theme that quietly goes half-un-styled.
