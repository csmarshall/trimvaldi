#!/usr/bin/env python3
"""Minimal Chrome DevTools Protocol client for mapping Vivaldi's UI DOM.

Usage:
    cdp.py <target-substring> <<'JS'
    <javascript expression>
    JS

Connects to the first DevTools target whose URL contains <target-substring>,
evaluates the JS expression in that context, and prints the result.
"""
import asyncio
import json
import sys
import urllib.request

import websockets

DEVTOOLS = "http://127.0.0.1:9222"


def find_target(substr):
    with urllib.request.urlopen(f"{DEVTOOLS}/json") as r:
        targets = json.load(r)
    for t in targets:
        if substr in t.get("url", "") and t.get("webSocketDebuggerUrl"):
            return t
    raise SystemExit(f"no target matching {substr!r}; "
                     f"have: {[t.get('url','')[:60] for t in targets]}")


async def evaluate(ws_url, expression):
    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        }))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                return msg


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    target = find_target(sys.argv[1])
    expression = sys.stdin.read()
    msg = asyncio.run(evaluate(target["webSocketDebuggerUrl"], expression))

    result = msg.get("result", {})
    if "exceptionDetails" in result:
        print("JS EXCEPTION:", json.dumps(result["exceptionDetails"], indent=2)[:2000])
        return
    value = result.get("result", {}).get("value")
    if isinstance(value, (dict, list)):
        print(json.dumps(value, indent=2))
    else:
        print(value)


if __name__ == "__main__":
    main()
