#!/usr/bin/env bash
# Orbitron · installer
#   ./install.sh                 interactive
#   ./install.sh --yes           no prompts
#   ./install.sh --dry-run       show what would happen, change nothing
# Options: --no-zed --no-icons --no-xcode --no-terminal --no-claude
#          --dark "Orbitron Eclipse"   --light "Orbitron Lunar"   (variants Zed follows with the system)
#          --plain (no colour / animation)   -h | --help
set -euo pipefail

ORB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ORB_ROOT
VERSION="$(tr -d '[:space:]' <"$ORB_ROOT/VERSION")"
MODE="${ORBITRON_MODE:-install}"

DO_ZED=1 DO_ICONS=1 DO_XCODE=1 DO_TERMINAL=1 DO_CLAUDE=1
ORB_YES=0 DRY=0
DARK_THEME="Orbitron" LIGHT_THEME="Orbitron Daylight"
while [ $# -gt 0 ]; do
  case "$1" in
    -y | --yes) ORB_YES=1 ;;
    -n | --dry-run) DRY=1 ;;
    --no-zed) DO_ZED=0 ;;
    --no-icons) DO_ICONS=0 ;;
    --no-xcode) DO_XCODE=0 ;;
    --no-terminal) DO_TERMINAL=0 ;;
    --no-claude) DO_CLAUDE=0 ;;
    --dark) DARK_THEME="${2:?--dark needs a name}"; shift ;;
    --light) LIGHT_THEME="${2:?--light needs a name}"; shift ;;
    --plain) export ORBITRON_PLAIN=1 ;;
    -h | --help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 64 ;;
  esac
  shift
done
export ORB_YES

# shellcheck source=lib/ui.sh
. "$ORB_ROOT/lib/ui.sh"
ui_init

TOOL="$ORB_ROOT/lib/tool.py"
ORB_HOME="${ORBITRON_HOME:-$HOME/.orbitron}"
STATE="$ORB_HOME/state.json"
BACKUP_DIR="$ORB_HOME/backups/$(date +%Y%m%d-%H%M%S)"
ZED_DIR="$HOME/.config/zed"
ZED_SUPPORT="$HOME/Library/Application Support/Zed"
EXT_ID="orbitron-icons"
EXT_SRC="$ORB_ROOT/zed/extension"
EXT_DIR="$ORB_HOME/zed-icons"                              # stable copy (survives moving this repo)
EXT_LINK="$ZED_SUPPORT/extensions/installed/$EXT_ID"       # Zed loads icon themes only from extensions
XCODE_DIR="$HOME/Library/Developer/Xcode/UserData/FontAndColorThemes"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
CLAUDE_JSON="$HOME/.claude.json"
DRYFLAG=""
W=""
[ "$DRY" = 1 ] && { DRYFLAG="--dry-run"; W="(dry run) "; }
ICONS_CHANGED=0
INSTALLED=()   # files we put on disk (recorded for uninstall)

py() { python3 -I "$TOOL" "$@"; }

# ───────────────────────────── preflight ─────────────────────────────
if [ "$MODE" = "update" ]; then banner "U P D A T E   ·   v$VERSION"; else banner "I N S T A L L   ·   v$VERSION"; fi
tagline

[ "$(uname -s)" = "Darwin" ] || die "Orbitron's installer targets macOS" "found $(uname -s)"
command -v python3 >/dev/null 2>&1 && python3 -I -c 'import sys; sys.exit(sys.version_info < (3, 8))' \
  || die "python3 (3.8+) is required" "xcode-select --install  ·  brew install python"
[ -f "$ORB_ROOT/zed/themes/orbitron.json" ] || die "theme files missing" "run: python3 -I scripts/build.py"

has_zed()    { [ -d /Applications/Zed.app ] || [ -d "$HOME/Applications/Zed.app" ] || [ -d "$ZED_DIR" ] || command -v zed >/dev/null 2>&1; }
has_xcode()  { ls -d /Applications/Xcode*.app >/dev/null 2>&1 || [ -d "$XCODE_DIR" ]; }
has_claude() { [ -f "$CLAUDE_SETTINGS" ] || [ -f "$CLAUDE_JSON" ] || command -v claude >/dev/null 2>&1; }

[ "$DO_ZED" = 1 ]    && ! has_zed    && { DO_ZED=0;    warn "Zed not found" "skipping"; }
[ "$DO_XCODE" = 1 ]  && ! has_xcode  && { DO_XCODE=0;  warn "Xcode not found" "skipping"; }
[ "$DO_CLAUDE" = 1 ] && ! has_claude && { DO_CLAUDE=0; warn "Claude Code not found" "skipping"; }

[ "$DO_ZED" = 0 ] && DO_ICONS=0

variants_table

TILDE='~'
printf '\n'
box_top "Plan"
box_row "  $([ "$DO_ZED" = 1 ] && echo "$G_OK" || echo "$G_SKIP")  Zed         5 themes · follows system light/dark" "$WHITE"
box_row "  $([ "$DO_ICONS" = 1 ] && echo "$G_OK" || echo "$G_SKIP")  Zed icons   5 icon themes · 560 file & folder icons" "$WHITE"
box_row "  $([ "$DO_XCODE" = 1 ] && echo "$G_OK" || echo "$G_SKIP")  Xcode       5 colour themes (editor + workspace)" "$WHITE"
box_row "  $([ "$DO_TERMINAL" = 1 ] && echo "$G_OK" || echo "$G_SKIP")  Terminal    5 Terminal.app profiles" "$WHITE"
box_row "  $([ "$DO_CLAUDE" = 1 ] && echo "$G_OK" || echo "$G_SKIP")  Claude Code ANSI theme → follows Zed's terminal palette" "$WHITE"
box_row "  ${G_INFO}  backups  → ${ORB_HOME/#$HOME/$TILDE}/backups" "$DIM"
[ "$DRY" = 1 ] && box_row "  ${G_WARN}  DRY RUN — nothing will be changed" "$AMBER"
box_bottom
printf '\n'

ask "Install Orbitron?" y || { printf '\n  %sNo changes made.%s\n\n' "$DIM" "$RST"; exit 0; }

# ───────────────────────────── helpers ─────────────────────────────
backup_file() {
  [ -f "$1" ] || return 0
  [ "$DRY" = 1 ] && return 0
  mkdir -p "$BACKUP_DIR"
  chmod 700 "$ORB_HOME" "$ORB_HOME/backups" "$BACKUP_DIR" 2>/dev/null || true
  local dest="$BACKUP_DIR/$(printf '%s' "$1" | sed "s|^$HOME/||; s|/|__|g")"
  [ -e "$dest" ] && return 0   # keep the pristine copy if we back the same file up twice in one run
  cp -p "$1" "$dest" && chmod 600 "$dest"
}

# copy_if_changed SRC DST → rc 0 copied, 2 already identical
copy_if_changed() {
  if [ -f "$2" ] && cmp -s "$1" "$2"; then return 2; fi
  if [ "$DRY" = 1 ]; then return 0; fi
  backup_file "$2"
  mkdir -p "$(dirname "$2")"
  cp "$1" "$2"
}

# ───────────────────────────── steps ─────────────────────────────
step_zed_files() {
  local rc=0
  copy_if_changed "$ORB_ROOT/zed/themes/orbitron.json" "$ZED_DIR/themes/orbitron.json" || rc=$?
  if [ "$rc" = 2 ]; then echo "orbitron.json already current"; return 2; fi
  echo "${W}orbitron.json · 5 themes → ~/.config/zed/themes"
}
step_zed_settings() {
  backup_file "$ZED_DIR/settings.json"
  # shellcheck disable=SC2086
  py zed-apply --settings "$ZED_DIR/settings.json" --light "$LIGHT_THEME" --dark "$DARK_THEME" --state "$STATE" $DRYFLAG
}
# Zed loads icon themes only from extensions. Install exactly like a "dev extension":
# a symlink in Zed's extensions/installed dir pointing at a stable copy under ~/.orbitron.
tree_sum() { (cd "$1" && find . -type f | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1); }
step_zed_icons_files() {
  local sum_file="$ORB_HOME/icons.sha" sum link_ok=0
  [ -d "$EXT_SRC/icons" ] || { echo "icon files missing — run: python3 -I scripts/build.py"; return 1; }
  sum=$(tree_sum "$EXT_SRC")
  if [ -e "$EXT_LINK" ] || [ -L "$EXT_LINK" ]; then
    if [ -L "$EXT_LINK" ] && [ "$(readlink "$EXT_LINK")" = "$EXT_DIR" ]; then link_ok=1
    else echo "an extension named $EXT_ID already exists; left alone"; return 1; fi
  fi
  if [ "$link_ok" = 1 ] && [ -d "$EXT_DIR" ] && [ -f "$sum_file" ] && [ "$(cat "$sum_file")" = "$sum" ]; then
    echo "icon extension already current"; return 2
  fi
  if [ "$DRY" = 1 ]; then echo "${W}5 icon themes → extension $EXT_ID"; return 0; fi
  mkdir -p "$ORB_HOME"
  rm -rf "$EXT_DIR.new"; cp -R "$EXT_SRC" "$EXT_DIR.new"; rm -rf "$EXT_DIR"; mv "$EXT_DIR.new" "$EXT_DIR"
  mkdir -p "$(dirname "$EXT_LINK")"
  ln -sfn "$EXT_DIR" "$EXT_LINK"
  printf '%s\n' "$sum" >"$sum_file"
  py state-set --state "$STATE" --key zed_ext --value "{\"link\": \"$EXT_LINK\", \"dir\": \"$EXT_DIR\"}" >/dev/null
  echo "5 icon themes · 560 SVGs → Zed extension $EXT_ID"
}
step_zed_icon_settings() {
  backup_file "$ZED_DIR/settings.json"
  # shellcheck disable=SC2086
  py zed-apply --key icon_theme --settings "$ZED_DIR/settings.json" --light "$LIGHT_THEME Icons" --dark "$DARK_THEME Icons" --state "$STATE" $DRYFLAG
}
step_xcode() {
  local f n=0 changed=0 rc
  for f in "$ORB_ROOT"/xcode/*; do
    rc=0; copy_if_changed "$f" "$XCODE_DIR/$(basename "$f")" || rc=$?
    n=$((n + 1)); [ "$rc" = 0 ] && changed=$((changed + 1))
  done
  if [ "$changed" = 0 ]; then echo "$n files already current"; return 2; fi
  echo "${W}$changed of $n files → Xcode FontAndColorThemes"
}
step_terminal_import() {
  local sum_file="$ORB_HOME/terminal.sha" sum f
  sum=$(cat "$ORB_ROOT"/terminal/*.terminal | shasum -a 256 | cut -d' ' -f1)
  if [ -f "$sum_file" ] && [ "$(cat "$sum_file")" = "$sum" ] && [ "${FORCE_TERMINAL:-0}" != 1 ]; then
    echo "profiles already imported"; return 2
  fi
  if [ "$DRY" = 1 ]; then echo "would import 5 profiles into Terminal.app"; return 0; fi
  if [ "${ORBITRON_SKIP_OPEN:-0}" != 1 ]; then
    for f in "$ORB_ROOT"/terminal/*.terminal; do open -g -a Terminal "$f"; sleep 0.4; done
  fi
  mkdir -p "$ORB_HOME"; printf '%s\n' "$sum" >"$sum_file"
  echo "5 profiles imported (close the extra windows Terminal opened)"
}
step_terminal_default() {
  [ "${ORBITRON_SKIP_OPEN:-0}" = 1 ] && { echo "skipped (test mode)"; return 2; }
  # shellcheck disable=SC2086
  py terminal-apply --profile "Orbitron" --state "$STATE" $DRYFLAG
}
step_claude() {
  # shellcheck disable=SC2086
  py claude-apply --settings "$CLAUDE_SETTINGS" --claude-json "$CLAUDE_JSON" --state "$STATE" $DRYFLAG
}
step_state() {
  local f
  [ "$DRY" = 1 ] && { echo "would record install state"; return 0; }
  INSTALLED=("$ZED_DIR/themes/orbitron.json")
  for f in "$ORB_ROOT"/xcode/*; do INSTALLED+=("$XCODE_DIR/$(basename "$f")"); done
  py state-files --state "$STATE" --version "$VERSION" "${INSTALLED[@]}" >/dev/null
  echo "~/.orbitron/state.json"
}

# ───────────────────────────── run ─────────────────────────────
TOTAL=1
[ "$DO_ZED" = 1 ] && TOTAL=$((TOTAL + 1))
[ "$DO_XCODE" = 1 ] && TOTAL=$((TOTAL + 1))
[ "$DO_TERMINAL" = 1 ] && TOTAL=$((TOTAL + 1))
[ "$DO_CLAUDE" = 1 ] && TOTAL=$((TOTAL + 1))
DONE=0
tick() { DONE=$((DONE + 1)); progress "$DONE" "$TOTAL" "$1"; }

if [ "$DO_ZED" = 1 ]; then
  section "Zed"
  task "Install theme file" step_zed_files
  if ask "Switch Zed to Orbitron (follows system light/dark)?" y; then
    task "Select Orbitron in settings.json" step_zed_settings
  else skip "Zed theme selection" "left as-is"; fi
  if [ "$DO_ICONS" = 1 ]; then
    task "Install icon extension" step_zed_icons_files
    [ "$TASK_RC" = 0 ] && [ "$DRY" != 1 ] && ICONS_CHANGED=1
    if { [ "$TASK_RC" = 0 ] || [ "$TASK_RC" = 2 ]; } && ask "Use Orbitron icons in Zed's project panel?" y; then
      task "Select Orbitron icons in settings.json" step_zed_icon_settings
    else skip "Zed icon theme" "left as-is"; fi
  fi
  tick "Zed"
fi
if [ "$DO_XCODE" = 1 ]; then
  section "Xcode"
  task "Install colour themes" step_xcode; tick "Xcode"
fi
if [ "$DO_TERMINAL" = 1 ]; then
  section "Terminal.app"
  if ask "Import Terminal.app profiles? (opens a window per profile)" y; then
    task "Import profiles" step_terminal_import
    if ask "Make \"Orbitron\" the default Terminal profile?" y; then
      task "Set default profile" step_terminal_default
    else skip "Default profile" "unchanged"; fi
  else skip "Terminal.app" "skipped"; fi
  tick "Terminal.app"
fi
if [ "$DO_CLAUDE" = 1 ]; then
  section "Claude Code"
  task "Use ANSI theme (inherits the terminal palette)" step_claude; tick "Claude Code"
fi
# Zed caches icon SVGs for the life of the process and never re-reads a changed extension folder.
if [ "$ICONS_CHANGED" = 1 ] && pgrep -f 'Zed.app/Contents/MacOS/zed' >/dev/null 2>&1; then
  warn "Zed is running — quit it with ⌘Q and reopen to load the new icons" "closing the window is not enough"
fi
section "Finish"
task "Record install state" step_state; tick "Done"

# ───────────────────────────── summary ─────────────────────────────
printf '\n'
if [ "$ORB_FAILS" -gt 0 ]; then
  box_top "Finished with issues"
  box_row "  $ORB_FAILS step(s) failed — details are shown above." "$RED"
  box_bottom
  printf '\n'
  exit 1
fi
box_top "$([ "$DRY" = 1 ] && echo "Dry run complete" || echo "Orbitron is in orbit")  ·  $(elapsed)s"
box_row "  Zed          ⌘K ⌘T themes · icons need a Zed restart" "$WHITE"
box_row "  Terminal     restart it → profile “Orbitron”" "$WHITE"
box_row "  Xcode        restart it → Settings ➜ Themes" "$WHITE"
box_row "  Claude Code  /theme → “Dark/Light mode (ANSI colors only)”" "$WHITE"
box_sep
box_row "  update      ./update.sh        remove   ./uninstall.sh" "$HIPINK"
box_bottom
printf '\n'
