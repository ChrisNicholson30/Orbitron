<div align="center">

```
 ██████╗ ██████╗ ██████╗ ██╗████████╗██████╗  ██████╗ ███╗   ██╗
██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
██║   ██║██████╔╝██████╔╝██║   ██║   ██████╔╝██║   ██║██╔██╗ ██║
██║   ██║██╔══██╗██╔══██╗██║   ██║   ██╔══██╗██║   ██║██║╚██╗██║
╚██████╔╝██║  ██║██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

**Space gray. Hot pink.** One palette for Zed, Xcode, Terminal.app and Claude Code.

</div>

Orbitron is a theme suite built from a single palette (`palettes/orbitron.json`). Five variants, three dark and two light, are generated for every target, so they always agree with each other.

## Variants

| Variant | Mode | Editor background | Lead | Character |
|---|---|---|---|---|
| **Orbitron** | dark | `#1f2025` | hot pink `#ff2d95` | The flagship. Cyan, violet and amber in support. |
| **Orbitron Eclipse** | dark | `#16171b` | electric cyan `#2de2e6` | Deeper space gray, with pink as the secondary. |
| **Orbitron Nebula** | dark | `#232430` | violet `#a78bfa` | Cool indigo gray, with pink and cyan as highlights. |
| **Orbitron Daylight** | light | `#f3f4f6` | pink `#d6196f` | Silver and crisp. |
| **Orbitron Lunar** | light | `#ece9e4` | rose `#c2447f` | Warm moon-paper gray, easy on the eyes. |

Every text and syntax colour is checked against its background (WCAG AA, 4.5:1; comments 3.5:1). `python3 -I scripts/build.py --check` enforces this.

## Install

```sh
git clone <this repo> Orbitron && cd Orbitron
./install.sh            # interactive
./install.sh --dry-run  # preview, change nothing
```

| Target | What happens |
|---|---|
| **Zed** | Copies `orbitron.json` (5 themes, all 190 theme keys) to `~/.config/zed/themes` and sets `theme` to follow the system: `Orbitron Daylight` in light mode, `Orbitron` in dark. Only the `theme` value in `settings.json` is edited; comments and other settings are left alone. |
| **Xcode** | Installs 5 `.xccolortheme` and 5 `.xcworkspacecolortheme` files. Restart Xcode, then choose one in Settings ➜ Themes. |
| **Terminal.app** | Imports 5 profiles and can make `Orbitron` the default. Terminal opens one window per imported profile, so close them afterwards. |
| **Claude Code** | Sets the theme to `dark-ansi` (if it isn't already). See below. |

Options: `--yes`, `--dry-run`, `--no-zed`, `--no-xcode`, `--no-terminal`, `--no-claude`, `--dark "Orbitron Nebula"`, `--light "Orbitron Lunar"`, `--plain`.

Everything the installer changes is backed up to `~/.orbitron/backups/` (owner-only permissions), and what it changed is recorded in `~/.orbitron/state.json` so that `uninstall.sh` can put it back.

## Claude Code inside Zed's terminal

Claude Code's *ANSI* themes (`/theme` ➜ “Dark mode (ANSI colors only)” or “Light mode (ANSI colors only)”) don't use their own colours. They use whatever your terminal's 16-colour palette says. Zed's terminal palette comes from the theme's `terminal.ansi.*` keys, so Claude Code recolours whenever you change the Zed theme.

Claude Code draws its brand accent (spinner, prompt marker) in **ANSI bright red**, so Orbitron makes *bright red* the lead pink in every variant. Magenta is violet so the two stay distinct. For light variants, pick the light ANSI option.

## Update and uninstall

```sh
./update.sh             # git pull --ff-only, then refresh only the files that changed
./update.sh --check     # just report whether an update exists
./uninstall.sh          # remove files, restore your previous Zed theme / Terminal default / Claude theme
./uninstall.sh --purge  # ...and delete ~/.orbitron (state + backups)
```

## Customising

Edit `palettes/orbitron.json`, then regenerate everything:

```sh
python3 -I scripts/build.py          # write all outputs
python3 -I scripts/build.py --check  # contrast + Zed key coverage + outputs up to date
```

```
palettes/orbitron.json   single source of truth (every colour, every variant)
scripts/build.py         generator + validator (Python standard library only)
scripts/zed_keys.txt     the Zed theme keys every variant must define
zed/  xcode/  terminal/  generated themes (committed, so installing needs no build)
lib/ui.sh, lib/tool.py   installer UI and the safe JSONC / defaults helpers
```

Requires macOS and `python3` 3.8+. `install.sh` works with the stock macOS bash 3.2.
