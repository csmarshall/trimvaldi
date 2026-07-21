#!/usr/bin/env bash
# Launch Vivaldi with the DevTools Protocol exposed, against a disposable dev profile,
# so the UI DOM can be mapped programmatically (see docs/dom-map.md).
#
# Vivaldi's UI is an ordinary web page, so everything is scriptable — no clicking.
#
#   ./tools/dev-browser.sh              launch (reuses .dev-profile/)
#   ./tools/dev-browser.sh --fresh      wipe the profile first, for a clean-slate map
#   ./tools/dev-browser.sh --stop       quit Vivaldi and exit
#
# Then query it:
#   ./tools/cdp.py window.html <<< 'document.querySelector("#browser").className'

unset TMOUT
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="$REPO/.dev-profile"          # gitignored
PORT="${VIVALDI_DEBUG_PORT:-9222}"
APP="/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"

stop_vivaldi() {
  osascript -e 'tell application "Vivaldi" to quit' 2>/dev/null || true
  for _ in $(seq 1 20); do
    pgrep -f 'MacOS/Vivaldi' >/dev/null || return 0
    sleep 0.4
  done
  pkill -f 'MacOS/Vivaldi' 2>/dev/null || true
  sleep 1
}

case "${1:-}" in
  --stop)  stop_vivaldi; echo "Vivaldi stopped."; exit 0 ;;
  --fresh) stop_vivaldi; rm -rf "$PROFILE"; echo "Wiped $PROFILE" ;;
  "")      ;;
  *)       sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 1 ;;
esac

[ -x "$APP" ] || { echo "ERROR: Vivaldi not found at $APP" >&2; exit 1; }

# Vivaldi owns its Preferences file and rewrites it on exit, so never launch a second
# instance against the same profile — and never hand-patch prefs while it is running.
if pgrep -f "user-data-dir=$PROFILE" >/dev/null; then
  echo "Already running against $PROFILE (port $PORT)."; exit 0
fi

mkdir -p "$PROFILE"
"$APP" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins='*' \
  --debug-packed-apps \
  --user-data-dir="$PROFILE" \
  --no-first-run \
  --no-default-browser-check \
  >"$REPO/.dev-profile/vivaldi.log" 2>&1 &

for _ in $(seq 1 40); do
  if curl -sq "http://127.0.0.1:$PORT/json" 2>/dev/null | grep -q window.html; then
    echo "Vivaldi up. DevTools on :$PORT, profile $PROFILE"
    echo "UI target: chrome-extension://mpognobbkildjkofajifpdfhcoklimli/window.html"
    exit 0
  fi
  sleep 0.5
done

echo "ERROR: DevTools never came up on :$PORT — see $PROFILE/vivaldi.log" >&2
exit 1
