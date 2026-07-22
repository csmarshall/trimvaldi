#!/usr/bin/env python3
"""Live-check every selector and Vivaldi variable trimvaldi depends on.

[ADR-0002] concentrates Vivaldi's DOM and variable names in css/00-selectors.css
because that dependency surface fails SILENTLY — a renamed class does not error,
it just quietly stops applying, and the result looks "slightly un-themed" rather
than broken. [ADR-0009] makes that surface machine-checkable: this tool parses the
registry out of the CSS comment and asserts each entry against a running Vivaldi.

It is the precondition for any future trimvaldi-drift: a monitor can only watch a
dependency surface that is enumerable in one place.

Usage:
    ./tools/dev-browser.sh              # or spike/setup.sh
    ./tools/verify-selectors.py         # exits non-zero if anything is missing
    ./tools/verify-selectors.py --json

Exit codes:  0 all good (or only skips)   1 failures   2 could not run
"""
import argparse
import asyncio
import json
import pathlib
import re
import sys
import urllib.request

try:
    import websockets
except ImportError:
    sys.exit("2: pip install websockets")

DEVTOOLS = "http://127.0.0.1:9222"
REPO = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_FILE = REPO / "css" / "00-selectors.css"

# A registry line: "@sel  name | selector | requires" (leading * or / tolerated).
ENTRY_RE = re.compile(r"^[\s*/]*@(sel|var)\s+(\S+)\s*\|\s*(.+?)\s*\|\s*(\S+)\s*$")

# Only lines BETWEEN these markers are parsed. Without them the format
# documentation above the registry — which necessarily contains a literal
# "@sel <name> | <selector> | <requires>" — parses as a bogus entry.
BEGIN_RE = re.compile(r"@registry-begin")
END_RE = re.compile(r"@registry-end")

# Which `requires` values the CURRENT browser state can actually satisfy. Anything
# else is SKIPPED rather than failed — the whole point of the requires field is to
# stop state-dependent entries reading as renames.
def satisfiable(requires, state):
    if requires == "always":
        return True
    if requires == "never":            # asserted absent, always checkable
        return True
    if requires == "tabs-left":
        return state["tabs_left"]
    if requires == "theme-light":
        return state["theme_light"]
    if requires == "page-loaded":
        return state["page_loaded"]
    if requires == "window-blurred":
        return state["window_blurred"]
    return False


def parse_registry(path):
    entries, inside = [], False
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if BEGIN_RE.search(line):
            inside = True
            continue
        if END_RE.search(line):
            inside = False
            continue
        if not inside:
            continue
        m = ENTRY_RE.match(line)
        if m:
            kind, name, value, requires = m.groups()
            entries.append({"kind": kind, "name": name, "value": value,
                            "requires": requires, "line": lineno})
    if inside:
        sys.exit(f"2: @registry-begin without @registry-end in {path}")
    return entries


def find_ui_target():
    with urllib.request.urlopen(f"{DEVTOOLS}/json", timeout=5) as r:
        for t in json.load(r):
            if "window.html" in t.get("url", "") and t.get("webSocketDebuggerUrl"):
                return t
    raise SystemExit("2: no Vivaldi UI target on :9222 — is dev-browser.sh running?")


async def evaluate(ws_url, expression):
    async with websockets.connect(ws_url, max_size=32 << 20) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expression, "returnByValue": True, "awaitPromise": True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                res = msg.get("result", {})
                if "exceptionDetails" in res:
                    raise SystemExit(f"2: JS error: {res['exceptionDetails']}")
                return res["result"]["value"]


PROBE = """
(() => {
  const b = document.querySelector('#browser');
  const cs = getComputedStyle(b);
  const state = {
    tabs_left:   /\\btabs-left\\b/.test(b.className),
    theme_light: /\\btheme-light\\b/.test(b.className),
    // A real page is loaded if the active tab is not a blank/internal one.
    page_loaded: !!document.querySelector('.BookmarkButton'),
    // Detected INDEPENDENTLY of Vivaldi's own class, or the check would be
    // circular: deriving "is it blurred?" from .isblurred would make the entry
    // pass whether or not Vivaldi still sets it.
    window_blurred: !document.hasFocus(),
  };
  const sel = {}, vars = {};
  for (const s of %SELECTORS%) {
    try { sel[s] = document.querySelectorAll(s).length; }
    catch (e) { sel[s] = -1; }              // -1 = invalid selector syntax
  }
  for (const v of %VARS%) vars[v] = cs.getPropertyValue(v).trim();
  return {state, sel, vars};
})()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    entries = parse_registry(REGISTRY_FILE)
    if not entries:
        sys.exit(f"2: no registry entries found in {REGISTRY_FILE}")

    selectors = sorted({e["value"] for e in entries if e["kind"] == "sel"})
    variables = sorted({e["value"] for e in entries if e["kind"] == "var"})

    target = find_ui_target()
    probe = (PROBE.replace("%SELECTORS%", json.dumps(selectors))
                  .replace("%VARS%", json.dumps(variables)))
    result = asyncio.run(evaluate(target["webSocketDebuggerUrl"], probe))
    state = result["state"]

    rows = []
    for e in entries:
        if e["kind"] == "sel":
            count = result["sel"].get(e["value"], 0)
            if count == -1:
                verdict, detail = "FAIL", "invalid selector syntax"
            elif e["requires"] == "never":
                verdict = "ok" if count == 0 else "FAIL"
                detail = f"{count} matches (expected none)"
            elif not satisfiable(e["requires"], state):
                verdict, detail = "skip", f"needs state: {e['requires']}"
            elif count > 0:
                verdict, detail = "ok", f"{count} matches"
            else:
                verdict, detail = "FAIL", "0 matches — renamed or removed?"
        else:
            value = result["vars"].get(e["value"], "")
            if e["requires"] == "never":
                verdict = "ok" if value == "" else "FAIL"
                detail = "undefined, as expected" if value == "" \
                         else f"now DEFINED as {value!r} — Vivaldi changed"
            elif not satisfiable(e["requires"], state):
                verdict, detail = "skip", f"needs state: {e['requires']}"
            elif value:
                verdict, detail = "ok", value
            else:
                verdict, detail = "FAIL", "resolves empty — renamed or removed?"
        rows.append({**e, "verdict": verdict, "detail": detail})

    failures = [r for r in rows if r["verdict"] == "FAIL"]
    skips = [r for r in rows if r["verdict"] == "skip"]

    if args.json:
        print(json.dumps({"state": state, "rows": rows,
                          "failed": len(failures), "skipped": len(skips)}, indent=2))
    else:
        print(f"Browser state: {', '.join(k for k, v in state.items() if v) or 'none'}\n")
        for r in rows:
            mark = {"ok": "  ok  ", "skip": " skip ", "FAIL": " FAIL "}[r["verdict"]]
            print(f"[{mark}] {r['kind']} {r['name']:<16} {r['value']:<46} {r['detail']}")
        print(f"\n{len(rows) - len(failures) - len(skips)} ok, "
              f"{len(skips)} skipped, {len(failures)} failed")
        if skips:
            print("\nSkipped entries need a browser state this run did not have. To cover"
                  "\nthem, re-run with the light theme active, vertical tabs on, and a"
                  "\nreal page loaded. Skips are NOT passes.")
        if failures:
            print("\nFAILURES — a Vivaldi rename or removal is the likely cause. Confirm"
                  "\nagainst the live DOM before editing css/00-selectors.css:")
            for r in failures:
                print(f"  {REGISTRY_FILE.name}:{r['line']}  {r['name']}  {r['value']}")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
