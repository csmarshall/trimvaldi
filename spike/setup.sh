#!/usr/bin/env bash
# SPIKE — throwaway. Scripted, zero-GUI-step setup of Vivaldi CSS UI modifications.
#
# Answers spike question 1: can a fresh profile be taken from nothing to
# "our CSS is rendering" with no clicking? Every step here is file-level.
#
#   spike/setup.sh                 fresh profile, patch, launch, verify
#   spike/setup.sh --keep-profile  don't wipe; re-patch and relaunch
#   spike/setup.sh --stop          quit Vivaldi
#
# ONE pref does the whole job, written while Vivaldi is NOT running:
#   <profile>/Default/Preferences  vivaldi.appearance.css_ui_mods_directory = <css dir>
#
# MEASURED on 8.1.4087.55, 2026-07-21: the `vivaldi-css-mods` experiment flag is
# NOT required. A control run with the flag deliberately absent still loaded the
# mods; a control run with the flag absent AND the directory pref absent did not.
# So the directory pref alone is load-bearing. (vivaldi-peek documents
# `vivaldi.features.css_mods`, which does not exist anywhere in this build —
# neither the UI bundle nor the framework binary. Presumably stale.)
#
# --with-flag still writes browser.enabled_labs_experiments into Local State, in
# case an older or future build does gate on it. Off by default: unverified need.
#
# Vivaldi owns both files and rewrites them on exit. Never patch a live profile.

unset TMOUT
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${VIVALDI_SPIKE_PROFILE:-$REPO/.dev-profile}"
CSSDIR="${VIVALDI_SPIKE_CSS:-$REPO/spike/css}"
PORT="${VIVALDI_DEBUG_PORT:-9222}"
APP="/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"
FLAG="${VIVALDI_CSS_MODS_FLAG:-vivaldi-css-mods@1}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

stop_vivaldi() {
  osascript -e 'tell application "Vivaldi" to quit' 2>/dev/null || true
  for _ in $(seq 1 25); do
    pgrep -f 'MacOS/Vivaldi' >/dev/null || return 0
    sleep 0.4
  done
  pkill -f 'MacOS/Vivaldi' 2>/dev/null || true
  sleep 1
}

KEEP=0
WITH_FLAG=0
for arg in "$@"; do
  case "$arg" in
    --stop)         stop_vivaldi; log "Vivaldi stopped."; exit 0 ;;
    --keep-profile) KEEP=1 ;;
    --with-flag)    WITH_FLAG=1 ;;
    *)              sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 1 ;;
  esac
done

[ -x "$APP" ] || { echo "ERROR: Vivaldi not found at $APP" >&2; exit 1; }
[ -d "$CSSDIR" ] || { echo "ERROR: css dir not found: $CSSDIR" >&2; exit 1; }

log "Ensuring Vivaldi is not running (it rewrites Preferences on exit)"
stop_vivaldi

if [ "$KEEP" -eq 0 ]; then
  log "Wiping profile for a genuinely fresh start: $PROFILE"
  rm -rf "$PROFILE"
fi
mkdir -p "$PROFILE/Default"

log "Patching Preferences  -> vivaldi.appearance.css_ui_mods_directory = $CSSDIR"
[ "$WITH_FLAG" -eq 1 ] && log "Patching Local State  -> browser.enabled_labs_experiments += $FLAG"
CSSDIR="$CSSDIR" FLAG="$FLAG" WITH_FLAG="$WITH_FLAG" python3 - "$PROFILE" <<'PY'
import json, os, sys, pathlib

profile = pathlib.Path(sys.argv[1])
cssdir  = os.environ["CSSDIR"]
flag    = os.environ["FLAG"]

def patch(path, mutate):
    """Read-modify-write a Chromium JSON pref file, creating it if absent.

    Absent is normal on a fresh profile: Chromium happily reads a
    partial file and merges its own defaults over the top.
    """
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    mutate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    print(f"  wrote {path}")

def set_flag(data):
    labs = data.setdefault("browser", {}).setdefault("enabled_labs_experiments", [])
    # Tolerate a pre-existing entry under either spelling (bare or @index).
    base = flag.split("@")[0]
    labs[:] = [e for e in labs if not e.split("@")[0] == base]
    labs.append(flag)

def set_mods_dir(data):
    # Dotted pref paths are nested objects in the Preferences file.
    data.setdefault("vivaldi", {}).setdefault("appearance", {})["css_ui_mods_directory"] = cssdir

if os.environ.get("WITH_FLAG") == "1":
    patch(profile / "Local State", set_flag)
patch(profile / "Default" / "Preferences", set_mods_dir)
PY

log "Launching Vivaldi (DevTools :$PORT)"
"$APP" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins='*' \
  --debug-packed-apps \
  --user-data-dir="$PROFILE" \
  --no-first-run \
  --no-default-browser-check \
  >"$PROFILE/vivaldi.log" 2>&1 &

for _ in $(seq 1 60); do
  if curl -sq "http://127.0.0.1:$PORT/json" 2>/dev/null | grep -q window.html; then
    log "UI up on :$PORT"
    exit 0
  fi
  sleep 0.5
done

echo "ERROR: DevTools never came up on :$PORT — see $PROFILE/vivaldi.log" >&2
exit 1
