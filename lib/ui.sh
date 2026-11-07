# shellcheck shell=bash
# Orbitron · shared terminal UI (bash 3.2 compatible, sourced by install/update/uninstall)
#
# Truecolor when the terminal supports it, 256-colour otherwise, plain text when
# piped, NO_COLOR is set, or ORBITRON_PLAIN=1.

case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
  *UTF-8* | *utf8* | *utf-8*) ;;
  *) export LC_CTYPE=en_US.UTF-8 ;;
esac

ESC=$'\033'
ORB_TTY=0
[ -t 1 ] && ORB_TTY=1
ORB_COLOR=$ORB_TTY
{ [ -n "${NO_COLOR:-}" ] || [ "${TERM:-dumb}" = "dumb" ] || [ "${ORBITRON_PLAIN:-0}" = "1" ]; } && ORB_COLOR=0
ORB_TRUE=0
case "${COLORTERM:-}" in *truecolor* | *24bit*) ORB_TRUE=1 ;; esac
case "${TERM_PROGRAM:-}" in iTerm.app | WezTerm | ghostty | vscode | Zed) ORB_TRUE=1 ;; esac
[ "${ORB_FORCE_TRUECOLOR:-0}" = "1" ] && ORB_TRUE=1

# fg R G B  → escape for a foreground colour;  bg R G B → background
_c256() { echo $((16 + 36 * ($1 * 5 / 255) + 6 * ($2 * 5 / 255) + ($3 * 5 / 255))); }
fg() {
  [ "$ORB_COLOR" = 1 ] || return 0
  if [ "$ORB_TRUE" = 1 ]; then printf '%s[38;2;%s;%s;%sm' "$ESC" "$1" "$2" "$3"; else printf '%s[38;5;%sm' "$ESC" "$(_c256 "$1" "$2" "$3")"; fi
}
bg() {
  [ "$ORB_COLOR" = 1 ] || return 0
  if [ "$ORB_TRUE" = 1 ]; then printf '%s[48;2;%s;%s;%sm' "$ESC" "$1" "$2" "$3"; else printf '%s[48;5;%sm' "$ESC" "$(_c256 "$1" "$2" "$3")"; fi
}
hexfg() { fg $((16#${1:0:2})) $((16#${1:2:2})) $((16#${1:4:2})); }
hexbg() { bg $((16#${1:0:2})) $((16#${1:2:2})) $((16#${1:4:2})); }

if [ "$ORB_COLOR" = 1 ]; then
  RST="${ESC}[0m"; BOLD="${ESC}[1m"; ITAL="${ESC}[3m"
else
  RST=""; BOLD=""; ITAL=""
fi
PINK=$(fg 255 45 149)
HIPINK=$(fg 255 90 168)
CYAN=$(fg 90 216 236)
VIOLET=$(fg 185 155 255)
GREEN=$(fg 142 230 168)
AMBER=$(fg 255 193 107)
RED=$(fg 255 92 122)
DIM=$(fg 112 116 137)
SOFT=$(fg 164 168 182)
WHITE=$(fg 236 238 244)

# glyphs (ASCII fallback with ORBITRON_ASCII=1)
if [ "${ORBITRON_ASCII:-0}" = "1" ]; then
  G_OK="+"; G_FAIL="x"; G_WARN="!"; G_INFO="*"; G_SKIP="-"; G_DOT="o"; G_ARROW=">"; G_H="-"; G_V="|"
  G_TL="+"; G_TR="+"; G_BL="+"; G_BR="+"; G_FULL="#"; G_EMPTY="."
  SPIN_FRAMES="| / - \\"
else
  G_OK="✔"; G_FAIL="✖"; G_WARN="⚠"; G_INFO="◆"; G_SKIP="○"; G_DOT="●"; G_ARROW="➜"; G_H="─"; G_V="│"
  G_TL="╭"; G_TR="╮"; G_BL="╰"; G_BR="╯"; G_FULL="█"; G_EMPTY="░"
  SPIN_FRAMES="⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏"
fi

UI_W=64  # inner width of boxes
ORB_LOG="${TMPDIR:-/tmp}/orbitron-$$.log"
ORB_OUT="${TMPDIR:-/tmp}/orbitron-$$.out"
ORB_START=$(date +%s)
ORB_FAILS=0
TASK_RC=0

ui_cursor_hide() { [ "$ORB_TTY" = 1 ] && printf '%s[?25l' "$ESC"; return 0; }
ui_cursor_show() { [ "$ORB_TTY" = 1 ] && printf '%s[?25h' "$ESC"; return 0; }
ui_cleanup() { ui_cursor_show; rm -f "$ORB_LOG" "$ORB_OUT" 2>/dev/null; return 0; }
ui_init() {
  : >"$ORB_LOG"
  trap 'ui_cleanup' EXIT
  trap 'ui_cleanup; printf "\n"; exit 130' INT TERM
  ui_cursor_hide
}

_nap() { [ "$ORB_TTY" = 1 ] && sleep "$1"; return 0; }
repeat() { local s="" i; for ((i = 0; i < $2; i++)); do s="$s$1"; done; printf '%s' "$s"; }

# ───────────────────────────── banner ─────────────────────────────
banner() {
  local sub="$1"
  local rows=(
    " ██████╗ ██████╗ ██████╗ ██╗████████╗██████╗  ██████╗ ███╗   ██╗"
    "██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║"
    "██║   ██║██████╔╝██████╔╝██║   ██║   ██████╔╝██║   ██║██╔██╗ ██║"
    "██║   ██║██╔══██╗██╔══██╗██║   ██║   ██╔══██╗██║   ██║██║╚██╗██║"
    "╚██████╔╝██║  ██║██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║ ╚████║"
    " ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝"
  )
  local stops=("255 45 149" "255 79 163" "234 100 203" "200 140 245" "150 180 252" "90 216 236")
  local i
  printf '\n'
  if [ "${ORBITRON_ASCII:-0}" = "1" ]; then
    printf '   %sO R B I T R O N%s\n' "$PINK$BOLD" "$RST"
  else
    for i in 0 1 2 3 4 5; do
      # shellcheck disable=SC2086
      printf '  %s%s%s\n' "$(fg ${stops[$i]})" "${rows[$i]}" "$RST"
      _nap 0.04
    done
  fi
  printf '  %s%s%s  %s·%s  %s%s%s\n\n' "$DIM" "$(repeat "$G_H" 3)" "$RST" "$PINK" "$RST" \
    "$SOFT" "$sub" "$RST"
}

tagline() { printf '  %sspace gray%s %s·%s %shot pink%s %s·%s %sZed%s %s·%s %sXcode%s %s·%s %sTerminal%s %s·%s %sClaude Code%s\n\n' \
  "$SOFT" "$RST" "$DIM" "$RST" "$HIPINK" "$RST" "$DIM" "$RST" "$CYAN" "$RST" "$DIM" "$RST" "$VIOLET" "$RST" "$DIM" "$RST" \
  "$GREEN" "$RST" "$DIM" "$RST" "$AMBER" "$RST"; }

# ───────────────────────────── boxes ─────────────────────────────
box_top() {  # box_top "Title"
  local t=" $1 " n=$((UI_W - ${#1} - 2))
  printf '  %s%s%s%s%s%s%s%s\n' "$DIM" "$G_TL" "$(repeat "$G_H" 2)" "$RST" "$PINK$BOLD$t$RST" "$DIM" "$(repeat "$G_H" $((n - 2)))$G_TR" "$RST"
}
box_row() {  # box_row "plain text" [colour]  — text must be plain (no escapes) for padding
  local txt="$1" col="${2:-}" pad
  pad=$((UI_W - ${#txt} - 2))
  [ "$pad" -lt 0 ] && pad=0
  printf '  %s%s%s %s%s%s%s %s%s%s\n' "$DIM" "$G_V" "$RST" "$col" "$txt" "$RST" "$(repeat ' ' "$pad")" "$DIM" "$G_V" "$RST"
}
box_sep() { printf '  %s%s%s%s%s\n' "$DIM" "$G_V" "$(repeat ' ' $((UI_W)))" "$G_V" "$RST"; }
box_bottom() { printf '  %s%s%s%s%s\n' "$DIM" "$G_BL" "$(repeat "$G_H" $((UI_W)))" "$G_BR" "$RST"; }
section() { printf '\n  %s%s%s %s%s%s\n' "$PINK" "$G_INFO" "$RST" "$BOLD$WHITE" "$1" "$RST"; }

# ───────────────────────────── status lines ─────────────────────────────
ok()   { printf '  %s%s%s %s%s\n' "$GREEN" "$G_OK" "$RST" "$1" "${2:+  $DIM$2$RST}"; }
fail() { printf '  %s%s%s %s%s\n' "$RED" "$G_FAIL" "$RST" "$1" "${2:+  $DIM$2$RST}"; }
warn() { printf '  %s%s%s %s%s\n' "$AMBER" "$G_WARN" "$RST" "$1" "${2:+  $DIM$2$RST}"; }
info() { printf '  %s%s%s %s%s\n' "$CYAN" "$G_INFO" "$RST" "$1" "${2:+  $DIM$2$RST}"; }
skip() { printf '  %s%s %s%s%s\n' "$DIM" "$G_SKIP" "$1" "${2:+  $2}" "$RST"; }
die()  { fail "$1" "${2:-}"; ui_cleanup; exit 1; }

# ───────────────────────────── spinner & tasks ─────────────────────────────
# task "label" cmd args…   — runs cmd with a spinner. stdout of cmd becomes the dim detail
# (last line). exit 0 → ✔, exit 2 → ○ (nothing to do), else ✖ (shows log tail).
task() {
  local label="$1"; shift
  local pid i=0 rc frame frames n detail
  : >"$ORB_OUT"
  if [ "$ORB_TTY" != 1 ] || [ "$ORB_COLOR" != 1 ]; then
    rc=0; "$@" >"$ORB_OUT" 2>>"$ORB_LOG" || rc=$?
  else
    ( "$@" >"$ORB_OUT" 2>>"$ORB_LOG" ) &
    pid=$!
    # shellcheck disable=SC2206
    frames=($SPIN_FRAMES); n=${#frames[@]}
    while kill -0 "$pid" 2>/dev/null; do
      frame=${frames[$((i % n))]}
      # pink → cyan sweep across frames
      printf '\r%s[2K  %s%s%s %s' "$ESC" "$(fg $((255 - (i % n) * 18)) $((45 + (i % n) * 19)) $((149 + (i % n) * 9)))" "$frame" "$RST" "$label"
      i=$((i + 1)); sleep 0.07
    done
    rc=0; wait "$pid" || rc=$?
    printf '\r%s[2K' "$ESC"
  fi
  detail=$(tail -n 1 "$ORB_OUT" 2>/dev/null)
  case $rc in
    0) ok "$label" "$detail" ;;
    2) skip "$label" "${detail:-nothing to do}" ;;
    *) fail "$label" "$detail"; tail -n 6 "$ORB_LOG" 2>/dev/null | sed "s/^/      ${DIM}/;s/\$/${RST}/"; ;;
  esac
  TASK_RC=$rc
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then ORB_FAILS=$((ORB_FAILS + 1)); fi
  return 0
}

# progress CURRENT TOTAL [label] — gradient bar
progress() {
  local cur=$1 tot=$2 label="${3:-}" width=34 filled i r g b out="" pct
  filled=$((cur * width / tot)); pct=$((cur * 100 / tot))
  for ((i = 0; i < width; i++)); do
    if [ "$i" -lt "$filled" ]; then
      r=$((255 - i * 165 / width)); g=$((45 + i * 171 / width)); b=$((149 + i * 87 / width))
      out="$out$(fg $r $g $b)$G_FULL"
    else
      out="$out$DIM$G_EMPTY"
    fi
  done
  printf '  %s%s  %s%3d%%%s  %s%s%s\n' "$out" "$RST" "$BOLD$WHITE" "$pct" "$RST" "$SOFT" "$label" "$RST"
}

# ───────────────────────────── swatches ─────────────────────────────
swatch_strip() {  # swatch_strip "rrggbb,rrggbb,…"
  local IFS=',' c out=""
  for c in $1; do
    if [ "$ORB_COLOR" = 1 ]; then out="$out$(hexbg "$c")  $RST "; else out="$out#$c "; fi
  done
  printf '%s' "$out"
}

# variants_table PALETTE_JSON TOOL_PY
variants_table() {
  local id name mode tag cols
  box_top "Variants"
  while IFS='|' read -r id name mode tag cols; do
    [ -n "$id" ] || continue
    local m="dark "; [ "$mode" = "light" ] && m="light"
    local lead sw vis pad
    lead="${cols#*,}"; lead="${lead%%,*}"
    if [ "$ORB_COLOR" = 1 ]; then sw=$(swatch_strip "$cols"); vis=54; else sw="lead #$lead"; vis=39; fi
    pad=$((UI_W - 2 - vis))
    printf '  %s%s%s %s%s%s %s%-18s%s %s%s%s %s%s %s%s%s\n' "$DIM" "$G_V" "$RST" "$(hexfg "$lead")" "$G_DOT" "$RST" \
      "$BOLD$WHITE" "$name" "$RST" "$DIM" "$m" "$RST" "$sw" "$(repeat ' ' "$pad")" "$DIM" "$G_V" "$RST"
    box_row "  $tag" "$SOFT"
  done < <(python3 -I "$ORB_ROOT/lib/tool.py" swatches --palette "$ORB_ROOT/palettes/orbitron.json")
  box_bottom
}

# ───────────────────────────── prompts & footer ─────────────────────────────
# ask "Question?" [default y|n]   — honours --yes
ask() {
  local q="$1" def="${2:-y}" ans hint="[Y/n]"
  [ "$def" = "n" ] && hint="[y/N]"
  if [ "${ORB_YES:-0}" = 1 ]; then return 0; fi
  if [ ! -t 0 ]; then [ "$def" = "y" ]; return; fi
  printf '  %s%s%s %s %s%s%s ' "$PINK" "$G_ARROW" "$RST" "$q" "$DIM" "$hint" "$RST"
  ui_cursor_show
  read -r ans
  ui_cursor_hide
  ans=$(printf '%s' "${ans:-$def}" | tr '[:upper:]' '[:lower:]')
  [ "${ans:0:1}" = "y" ]
}

elapsed() { echo $(($(date +%s) - ORB_START)); }
