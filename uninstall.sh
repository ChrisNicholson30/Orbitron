#!/usr/bin/env bash
# Orbitron · uninstaller — removes what install.sh added and restores what it changed.
#   ./uninstall.sh              interactive
#   ./uninstall.sh --yes        no prompts
#   ./uninstall.sh --dry-run    show what would be removed
#   ./uninstall.sh --purge      also delete ~/.orbitron (state + backups)
set -euo pipefail

ORB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ORB_ROOT
ORB_YES=0 DRY=0 PURGE=0
for a in "$@"; do
  case "$a" in
    -y | --yes) ORB_YES=1 ;;
    -n | --dry-run) DRY=1 ;;
    --purge) PURGE=1 ;;
    --plain) export ORBITRON_PLAIN=1 ;;
    -h | --help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $a (try --help)" >&2; exit 64 ;;
  esac
done
export ORB_YES

# shellcheck source=lib/ui.sh
. "$ORB_ROOT/lib/ui.sh"
ui_init

ORB_HOME="${ORBITRON_HOME:-$HOME/.orbitron}"
STATE="$ORB_HOME/state.json"
ZED_DIR="$HOME/.config/zed"
XCODE_DIR="$HOME/Library/Developer/Xcode/UserData/FontAndColorThemes"
DRYFLAG=""; W=""
[ "$DRY" = 1 ] && { DRYFLAG="--dry-run"; W="(dry run) "; }
py() { python3 -I "$ORB_ROOT/lib/tool.py" "$@"; }

banner "U N I N S T A L L"
command -v python3 >/dev/null 2>&1 || die "python3 is required"

# Files to remove: from the install state, else fall back to well-known names.
FILES=()
if [ -f "$STATE" ]; then
  while IFS= read -r f; do [ -n "$f" ] && FILES+=("$f"); done < <(py state-get --state "$STATE" --key files 2>/dev/null || true)
else
  warn "No install state found" "falling back to well-known Orbitron files"
fi
if [ "${#FILES[@]}" = 0 ]; then
  [ -f "$ZED_DIR/themes/orbitron.json" ] && FILES+=("$ZED_DIR/themes/orbitron.json")
  for f in "$XCODE_DIR"/Orbitron*.xc*colortheme; do [ -e "$f" ] && FILES+=("$f"); done
fi

# Safety: only ever delete files whose name starts with "orbitron" inside the HOME tree.
safe_remove() {
  local f="$1" base
  base="$(basename "$f" | tr '[:upper:]' '[:lower:]')"
  case "$f" in "$HOME"/*) ;; *) echo "refusing path outside HOME"; return 1 ;; esac
  case "$base" in orbitron*) ;; *) echo "refusing non-Orbitron file"; return 1 ;; esac
  [ -e "$f" ] || return 2
  [ "$DRY" = 1 ] || rm -f "$f"
  echo "${W}removed $(basename "$f")"
}

box_top "This will"
box_row "  ${G_ARROW}  remove ${#FILES[@]} Orbitron theme file(s) (Zed, Xcode)" "$WHITE"
box_row "  ${G_ARROW}  restore your previous Zed theme, Terminal default, Claude theme" "$WHITE"
box_row "  ${G_ARROW}  remove Orbitron profiles from Terminal.app (if it is closed)" "$WHITE"
[ "$PURGE" = 1 ] && box_row "  ${G_WARN}  delete ~/.orbitron including backups (--purge)" "$AMBER"
[ "$DRY" = 1 ] && box_row "  ${G_WARN}  DRY RUN — nothing will be changed" "$AMBER"
box_bottom
printf '\n'
ask "Uninstall Orbitron?" n || { printf '\n  %sNo changes made.%s\n\n' "$DIM" "$RST"; exit 0; }

section "Restore settings"
task "Zed theme" py zed-restore --state "$STATE" $DRYFLAG
task "Claude Code theme" py claude-restore --state "$STATE" $DRYFLAG
if [ "${ORBITRON_SKIP_OPEN:-0}" != 1 ]; then
  task "Terminal.app default profile" py terminal-restore --state "$STATE" $DRYFLAG
fi

section "Remove files"
for f in ${FILES[@]+"${FILES[@]}"}; do
  task "$(basename "$f")" safe_remove "$f"
done
if [ "${ORBITRON_SKIP_OPEN:-0}" != 1 ]; then
  if pgrep -x Terminal >/dev/null 2>&1; then
    warn "Terminal.app is running" "quit it and re-run, or delete Orbitron profiles in Terminal ➜ Settings ➜ Profiles"
  else
    task "Terminal.app profiles" py terminal-remove $DRYFLAG
  fi
fi

section "Clean up"
if [ "$DRY" != 1 ]; then
  rm -f "$ORB_HOME/terminal.sha"
  py state-clear --state "$STATE" >/dev/null 2>&1 || true
fi
if [ "$PURGE" = 1 ]; then
  [ "$DRY" = 1 ] || rm -rf "$ORB_HOME"
  ok "${W}Deleted ~/.orbitron"
elif [ -d "$ORB_HOME/backups" ]; then
  info "Backups kept" "~/.orbitron/backups  (delete with: rm -rf ~/.orbitron)"
fi

printf '\n'
if [ "$ORB_FAILS" -gt 0 ]; then
  box_top "Finished with issues"; box_row "  $ORB_FAILS step(s) failed — details above." "$RED"; box_bottom; printf '\n'; exit 1
fi
box_top "Orbitron has left orbit"
box_row "  Restart Zed / Terminal / Xcode if they were open." "$WHITE"
box_row "  Reinstall any time with ./install.sh" "$HIPINK"
box_bottom
printf '\n'
