#!/usr/bin/env bash
# Orbitron · updater
#   ./update.sh            pull the latest release (git checkout) and refresh installed files
#   ./update.sh --check    only report whether an update is available
# Other options are passed to install.sh (e.g. --no-xcode, --dark "Orbitron Nebula").
set -euo pipefail

ORB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ORB_ROOT
CHECK_ONLY=0
PASS=()
for a in "$@"; do
  case "$a" in
    --check) CHECK_ONLY=1 ;;
    --plain) export ORBITRON_PLAIN=1; PASS+=("$a") ;;
    -h | --help) sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) PASS+=("$a") ;;
  esac
done

# shellcheck source=lib/ui.sh
. "$ORB_ROOT/lib/ui.sh"
ui_init

ORB_HOME="${ORBITRON_HOME:-$HOME/.orbitron}"
STATE="$ORB_HOME/state.json"
py() { python3 -I "$ORB_ROOT/lib/tool.py" "$@"; }
repo_version() { tr -d '[:space:]' <"$ORB_ROOT/VERSION"; }

banner "U P D A T E"

OLD="$(py state-get --state "$STATE" --key version 2>/dev/null || true)"
[ -n "$OLD" ] || warn "Orbitron isn't installed yet" "update will perform a fresh install"

IS_GIT=0
git -C "$ORB_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 && IS_GIT=1

fetch_updates() {
  git -C "$ORB_ROOT" remote | grep -q . || { echo "no git remote configured"; return 2; }
  git -C "$ORB_ROOT" fetch --quiet
  echo "fetched"
}
pull_updates() {
  local up
  up="$(git -C "$ORB_ROOT" rev-parse --abbrev-ref '@{u}' 2>/dev/null)" || { echo "no upstream branch"; return 2; }
  if [ -n "$(git -C "$ORB_ROOT" status --porcelain)" ]; then echo "local changes present; not pulling"; return 2; fi
  git -C "$ORB_ROOT" merge --ff-only --quiet "$up"
  echo "now at $(git -C "$ORB_ROOT" rev-parse --short HEAD)"
}

if [ "$IS_GIT" = 1 ]; then
  section "Checking for updates"
  task "Fetch from remote" fetch_updates
  BEHIND="$(git -C "$ORB_ROOT" rev-list --count 'HEAD..@{u}' 2>/dev/null || echo 0)"
  if [ "$BEHIND" -gt 0 ]; then
    info "$BEHIND new commit(s) available"
    git -C "$ORB_ROOT" log --oneline --no-decorate 'HEAD..@{u}' | head -n 8 | sed "s/^/      ${DIM}/;s/\$/${RST}/"
    if [ "$CHECK_ONLY" = 1 ]; then printf '\n'; exit 0; fi
    task "Pull latest" pull_updates
  else
    ok "Already on the latest commit"
    [ "$CHECK_ONLY" = 1 ] && { printf '\n'; exit 0; }
  fi
else
  warn "Not a git checkout" "re-download Orbitron to get new versions, then run ./install.sh"
  [ "$CHECK_ONLY" = 1 ] && { printf '\n'; exit 0; }
fi

NEW="$(repo_version)"
printf '\n'
box_top "Version"
box_row "  installed  ${OLD:-none}" "$SOFT"
box_row "  available  $NEW  $([ "${OLD:-}" = "$NEW" ] && echo '(same — refreshing files anyway)' || echo "${G_ARROW} updating")" "$HIPINK"
box_bottom
printf '\n'

# Re-run the installer non-interactively; it only rewrites files that actually changed.
# (Terminal.app profiles are re-imported only when their content changed.)
export ORBITRON_MODE=update
exec "$ORB_ROOT/install.sh" --yes ${PASS[@]+"${PASS[@]}"}
