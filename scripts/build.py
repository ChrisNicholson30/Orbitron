#!/usr/bin/env python3
"""Orbitron build: render every theme target from palettes/orbitron.json.

    python3 -I scripts/build.py            # (re)generate all outputs
    python3 -I scripts/build.py --check    # verify contrast, Zed key coverage, outputs up to date

Standard library only.
"""
import colorsys
import json
import math
import plistlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ROOT / "palettes" / "orbitron.json"
ZED_KEYS = ROOT / "scripts" / "zed_keys.txt"

# ───────────────────────────── colour helpers ─────────────────────────────


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x))) for x in c)


def mix(a, b, t):
    """Blend a toward b by t (0..1)."""
    ra, rb = rgb(a), rgb(b)
    return hexs(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def alpha(h, a):
    return "%s%02x" % (h[:7], round(a * 255))


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(h):
    r, g, b = rgb(h)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def oklch(h):
    """sRGB hex -> (L, C, hue radians) in OKLCH."""
    r, g, b = (lin(x) for x in rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B), math.atan2(B, A) % (2 * math.pi)


def best_on(bg, *cands):
    return max(cands, key=lambda c: contrast(bg, c))


# ───────────────────────────── Zed ─────────────────────────────

ANSI_NAMES = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]


def zed_style(v):
    bg, tx, ld, sy, st = v["bg"], v["text"], v["lead"], v["syn"], v["status"]
    dark = v["mode"] == "dark"
    fg = tx["fg"]
    base, panel, crust, surface, raised, border = (bg[k] for k in ("base", "panel", "crust", "surface", "raised", "border"))
    lead = ld["main"]
    accent_text = ld["hi"]
    clear = "#00000000"
    border_var = mix(border, base, 0.5)
    disabled = mix(tx["placeholder"], base, 0.45)
    on_lead = best_on(lead, crust, "#ffffff")
    ansi = {}
    for i, n in enumerate(ANSI_NAMES):
        ansi["terminal.ansi." + n] = v["ansi"][i]
        ansi["terminal.ansi.bright_" + n] = v["ansi"][i + 8]
        ansi["terminal.ansi.dim_" + n] = mix(v["ansi"][i], base, 0.38)
    git = {
        "created": st["success"], "deleted": st["error"], "modified": st["warning"],
        "renamed": st["info"], "conflict": sy["special"],
    }
    s = {
        "background.appearance": "opaque",
        "accents": [lead, st["info"], sy["ty"], sy["num"], st["success"], sy["prop"]],
        # surfaces
        "background": panel, "surface.background": panel, "elevated_surface.background": raised,
        "title_bar.background": crust, "title_bar.inactive_background": panel,
        "status_bar.background": crust, "toolbar.background": base,
        "tab_bar.background": panel, "tab.inactive_background": panel, "tab.active_background": base,
        "panel.background": panel, "panel.focused_border": lead, "panel.overlay_background": raised,
        "panel.overlay_hover": surface, "panel.indent_guide": alpha(border, 0.5),
        "panel.indent_guide_hover": alpha(border, 0.9), "panel.indent_guide_active": alpha(lead, 0.55),
        "pane.focused_border": lead, "pane_group.border": border,
        "drop_target.background": alpha(lead, 0.18), "drop_target.border": lead,
        # borders
        "border": border, "border.variant": border_var, "border.focused": lead,
        "border.selected": mix(lead, base, 0.45), "border.transparent": clear, "border.disabled": border_var,
        # elements
        "element.background": surface, "element.hover": mix(surface, border, 0.5),
        "element.active": border, "element.selected": mix(surface, lead, 0.2),
        "element.disabled": mix(surface, base, 0.5), "element.selection_background": alpha(lead, 0.26),
        "ghost_element.background": clear, "ghost_element.hover": alpha(fg, 0.07),
        "ghost_element.active": alpha(fg, 0.12), "ghost_element.selected": alpha(lead, 0.18),
        "ghost_element.disabled": alpha(fg, 0.03),
        # text & icons
        "text": fg, "text.muted": tx["muted"], "text.placeholder": tx["placeholder"],
        "text.disabled": disabled, "text.accent": accent_text,
        "icon": mix(fg, tx["muted"], 0.4), "icon.muted": tx["muted"], "icon.disabled": disabled,
        "icon.placeholder": tx["placeholder"], "icon.accent": accent_text,
        "link_text.hover": st["info"],
        # editor
        "editor.background": base, "editor.foreground": fg, "editor.gutter.background": base,
        "editor.subheader.background": panel, "editor.active_line.background": alpha(fg, 0.05),
        "editor.highlighted_line.background": alpha(lead, 0.10), "editor.debugger_active_line.background": alpha(st["warning"], 0.2),
        "editor.line_number": tx["placeholder"], "editor.active_line_number": fg,
        "editor.hover_line_number": tx["muted"], "editor.wrap_guide": alpha(border, 0.5),
        "editor.active_wrap_guide": border, "editor.indent_guide": alpha(border, 0.65),
        "editor.indent_guide_active": alpha(lead, 0.55), "editor.invisible": alpha(tx["placeholder"], 0.6),
        "editor.code_lens.foreground": tx["muted"],
        "editor.document_highlight.read_background": alpha(lead, 0.12),
        "editor.document_highlight.write_background": alpha(lead, 0.24),
        "editor.document_highlight.bracket_background": alpha(lead, 0.30),
        "editor.diff_hunk.added.background": alpha(st["success"], 0.12),
        "editor.diff_hunk.added.hollow_background": clear,
        "editor.diff_hunk.added.hollow_border": alpha(st["success"], 0.55),
        "editor.diff_hunk.deleted.background": alpha(st["error"], 0.12),
        "editor.diff_hunk.deleted.hollow_background": clear,
        "editor.diff_hunk.deleted.hollow_border": alpha(st["error"], 0.55),
        "search.match_background": alpha(sy["num"], 0.32), "search.active_match_background": alpha(lead, 0.5),
        # scrollbar & minimap
        "scrollbar.thumb.background": alpha(fg, 0.12), "scrollbar.thumb.hover_background": alpha(fg, 0.20),
        "scrollbar.thumb.active_background": alpha(fg, 0.28), "scrollbar.thumb.border": clear,
        "scrollbar.track.background": clear, "scrollbar.track.border": border_var,
        "minimap.thumb.background": alpha(fg, 0.08), "minimap.thumb.hover_background": alpha(fg, 0.14),
        "minimap.thumb.active_background": alpha(fg, 0.20), "minimap.thumb.border": alpha(border, 0.6),
        # status colours
        "hidden": tx["placeholder"], "ignored": tx["placeholder"], "unreachable": tx["placeholder"],
        "hint": tx["muted"], "hint.background": alpha(tx["muted"], 0.12), "hint.border": alpha(tx["muted"], 0.4),
        "predictive": tx["placeholder"], "predictive.background": clear, "predictive.border": alpha(tx["placeholder"], 0.4),
        "debugger.accent": lead,
        # terminal
        "terminal.background": base, "terminal.foreground": fg,
        "terminal.bright_foreground": v["ansi"][15] if dark else fg,
        "terminal.dim_foreground": tx["muted"], "terminal.ansi.background": base,
        # version control
        "version_control.added": st["success"], "version_control.deleted": st["error"],
        "version_control.modified": st["warning"], "version_control.renamed": st["info"],
        "version_control.conflict": sy["special"], "version_control.ignored": tx["placeholder"],
        "version_control.word_added": alpha(st["success"], 0.30), "version_control.word_deleted": alpha(st["error"], 0.30),
        "version_control.conflict_marker.ours": alpha(st["info"], 0.14),
        "version_control.conflict_marker.theirs": alpha(lead, 0.14),
        # vim
        "vim.normal.background": lead, "vim.normal.foreground": on_lead,
        "vim.insert.background": st["success"], "vim.insert.foreground": best_on(st["success"], crust, "#ffffff"),
        "vim.replace.background": st["error"], "vim.replace.foreground": best_on(st["error"], crust, "#ffffff"),
        "vim.visual.background": sy["ty"], "vim.visual.foreground": best_on(sy["ty"], crust, "#ffffff"),
        "vim.visual_line.background": sy["ty"], "vim.visual_line.foreground": best_on(sy["ty"], crust, "#ffffff"),
        "vim.visual_block.background": sy["ty"], "vim.visual_block.foreground": best_on(sy["ty"], crust, "#ffffff"),
        "vim.yank.background": alpha(sy["num"], 0.30),
        "vim.helix_normal.background": lead, "vim.helix_normal.foreground": on_lead,
        "vim.helix_select.background": st["info"], "vim.helix_select.foreground": best_on(st["info"], crust, "#ffffff"),
        "vim.helix_jump_label.foreground": sy["special"],
    }
    quiet = {"hidden": tx["placeholder"], "ignored": tx["placeholder"], "unreachable": tx["placeholder"]}
    for k, c in {**st, **git, **quiet}.items():
        s[k] = c
        s[k + ".background"] = alpha(c, 0.14)
        s[k + ".border"] = alpha(c, 0.45)
    s.update(ansi)
    # players: cursor / background / selection
    pcols = [lead, st["info"], sy["ty"], st["success"], sy["num"], sy["prop"], sy["param"], st["error"]]
    s["players"] = [{"cursor": c, "background": c, "selection": alpha(c, 0.26)} for c in pcols]

    def t(color, style=None, weight=None):
        return {"color": color, "font_style": style, "font_weight": weight}

    s["syntax"] = {
        "attribute": t(sy["attr"]), "boolean": t(sy["num"]),
        "comment": t(sy["cmt"], "italic"), "comment.doc": t(sy["doc"], "italic"),
        "comment.documentation": t(sy["doc"], "italic"),
        "constant": t(sy["num"]), "constructor": t(sy["ty"]),
        "diff.plus": t(st["success"]), "diff.minus": t(st["error"]),
        "embedded": t(fg), "emphasis": t(sy["fn"], "italic"), "emphasis.strong": t(sy["kw"], None, 700),
        "enum": t(sy["ty"]),
        "function": t(sy["fn"]), "function.builtin": t(sy["fn"]), "function.method": t(sy["fn"]),
        "function.special": t(sy["special"]),
        "hint": t(tx["muted"]),
        "keyword": t(sy["kw"]), "keyword.control": t(sy["kw"]), "keyword.operator": t(sy["op"]),
        "label": t(sy["label"]), "link_text": t(sy["link"]), "link_uri": t(sy["link"]),
        "markup.list": t(sy["op"]), "markup.list.checked": t(st["success"]), "markup.list.unchecked": t(tx["muted"]),
        "namespace": t(sy["ty"]), "number": t(sy["num"]), "operator": t(sy["op"]),
        "predictive": t(tx["placeholder"], "italic"), "preproc": t(sy["special"]), "primary": t(fg),
        "property": t(sy["prop"]),
        "punctuation": t(sy["punct"]), "punctuation.bracket": t(sy["punct"]),
        "punctuation.delimiter": t(sy["punct"]), "punctuation.list_marker": t(sy["op"]),
        "punctuation.markup": t(sy["op"]), "punctuation.special": t(sy["special"]),
        "selector": t(sy["tag"]), "selector.pseudo": t(sy["label"]),
        "string": t(sy["str"]), "string.escape": t(sy["esc"]), "string.regex": t(sy["rx"]),
        "string.special": t(sy["special"]), "string.special.symbol": t(sy["special"]),
        "tag": t(sy["tag"]), "text.literal": t(sy["str"]), "title": t(sy["kw"], None, 700),
        "type": t(sy["ty"]), "variable": t(fg), "variable.builtin": t(sy["kw"]),
        "variable.parameter": t(sy["param"]), "variable.special": t(sy["special"]),
        "variant": t(sy["ty"]),
    }
    return s


def render_zed(pal):
    themes = [{"name": v["name"], "appearance": v["mode"], "style": zed_style(v)} for v in pal["variants"]]
    doc = {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Orbitron", "author": pal["meta"]["author"], "themes": themes,
    }
    return (json.dumps(doc, indent=2) + "\n").encode()


# ───────────────────────────── Xcode ─────────────────────────────


def xc(h):
    r, g, b = (x / 255 for x in rgb(h))
    return "%.6f %.6f %.6f 1" % (r, g, b)


def xcode_theme(v):
    bg, tx, ld, sy, st = v["bg"], v["text"], v["lead"], v["syn"], v["status"]
    fg, base = tx["fg"], bg["base"]
    sel = mix(base, ld["main"], 0.28 if v["mode"] == "dark" else 0.22)
    cur = mix(base, fg, 0.06)
    syntax = {
        "attribute": sy["attr"], "character": sy["num"], "comment": sy["cmt"], "comment.doc": sy["doc"],
        "comment.doc.keyword": sy["doc"], "declaration.other": sy["fn"], "declaration.type": sy["ty"],
        "identifier.class": sy["ty"], "identifier.class.system": sy["ty"],
        "identifier.constant": sy["special"], "identifier.constant.system": sy["special"],
        "identifier.function": sy["fn"], "identifier.function.system": sy["fn"],
        "identifier.macro": sy["rx"], "identifier.macro.system": sy["rx"],
        "identifier.type": sy["ty"], "identifier.type.system": sy["ty"],
        "identifier.variable": sy["prop"], "identifier.variable.system": sy["prop"],
        "keyword": sy["kw"], "mark": ld["hi"], "markup.aside.kind": sy["kw"], "markup.code": sy["str"],
        "number": sy["num"], "plain": fg, "preprocessor": sy["rx"], "string": sy["str"], "url": sy["link"],
    }
    d = {
        "DVTFontAndColorVersion": 1,
        "DVTLineSpacing": 1,
        "DVTSourceTextBackground": xc(base),
        "DVTSourceTextCurrentLineHighlightColor": xc(cur),
        "DVTSourceTextSelectionColor": xc(sel),
        "DVTSourceTextBlockDimBackgroundColor": xc(bg["panel"]),
        "DVTSourceTextInvisiblesColor": xc(tx["placeholder"]),
        "DVTSourceTextSyntaxColors": {"xcode.syntax." + k: xc(c) for k, c in syntax.items()},
        "DVTSourceTextSyntaxFonts": {"xcode.syntax.plain": "SFMono-Regular - 12.0"},
        "DVTConsoleTextBackgroundColor": xc(bg["panel"]),
        "DVTConsoleTextSelectionColor": xc(sel),
        "DVTConsoleTextInsertionPointColor": xc(ld["main"]),
        "DVTConsoleDebuggerInputTextColor": xc(sy["fn"]),
        "DVTConsoleDebuggerOutputTextColor": xc(tx["muted"]),
        "DVTConsoleDebuggerPromptTextColor": xc(ld["hi"]),
        "DVTConsoleExectuableInputTextColor": xc(fg),
        "DVTConsoleExectuableOutputTextColor": xc(tx["muted"]),
        "DVTMarkupTextBackgroundColor": xc(bg["panel"]),
        "DVTMarkupTextBorderColor": xc(bg["border"]),
        "DVTMarkupTextNormalColor": xc(fg),
        "DVTMarkupTextEmphasisColor": xc(fg),
        "DVTMarkupTextStrongColor": xc(fg),
        "DVTMarkupTextLinkColor": xc(sy["link"]),
        "DVTMarkupTextInlineCodeColor": xc(sy["str"]),
        "DVTScrollbarMarkerErrorColor": xc(st["error"]),
        "DVTScrollbarMarkerWarningColor": xc(st["warning"]),
        "DVTScrollbarMarkerDiffColor": xc(st["info"]),
        "DVTScrollbarMarkerBreakpointColor": xc(ld["main"]),
    }
    return d


def ok(h, with_opacity=False):
    L, C, H = oklch(h)
    body = {"chroma": {"exact": C}, "gamut": "sRGB", "hue": {"radians": H}, "lightness": {"exact": L}, "opacity": 1}
    return body


def xcode_workspace(v):
    bg, tx, ld, sy, st = v["bg"], v["text"], v["lead"], v["syn"], v["status"]
    fg, base = tx["fg"], bg["base"]
    sel = mix(base, ld["main"], 0.28 if v["mode"] == "dark" else 0.22)
    cur = mix(base, fg, 0.06)
    ov = {
        "comment": sy["cmt"], "commentEmphasized": sy["doc"], "keyword": sy["kw"], "keyword.attribute": sy["attr"],
        "link": sy["link"], "markdown": fg, "markdownEmphasized": fg, "memberDeclaration": sy["fn"],
        "number": sy["num"], "number.character": sy["num"],
        "otherMember": sy["prop"], "otherMember.constant": sy["special"], "otherMember.function": sy["fn"],
        "otherMember.variable": sy["prop"], "otherType": sy["ty"], "otherType.class": sy["ty"], "otherType.type": sy["ty"],
        "plainText": fg, "preprocessor": sy["rx"], "preprocessor.macro": sy["rx"], "preprocessor.macroSystem": sy["rx"],
        "projectMember": sy["prop"], "projectMember.constant": sy["special"], "projectMember.function": sy["fn"],
        "projectMember.variable": sy["prop"], "projectType": sy["ty"], "projectType.class": sy["ty"],
        "projectType.type": sy["ty"], "string": sy["str"], "string.regex": sy["rx"], "typeDeclaration": sy["ty"],
        "debugger": ld["hi"], "diffAddition": st["success"], "diffDeletion": st["error"],
        "insertionPointColor": ld["main"], "invisibles": tx["placeholder"],
        "currentLineHighlight": cur, "selectedTextBackgroundColor": sel,
    }
    return {
        "fileVersion": 1,
        "recipe": {
            "background": {"customColor": ok(base)},
            "colorScheme": v["mode"],
            "palette": {
                "colorOverrides": {k: {"color": ok(c)} for k, c in ov.items()},
                "primary": {"custom": ok(bg["surface"])},
                "secondary": {"custom": ok(bg["panel"])},
            },
        },
    }


# ───────────────────────────── Terminal.app ─────────────────────────────


def ns_color(h):
    r, g, b = (x / 255 for x in rgb(h))
    arch = {
        "$version": 100000, "$archiver": "NSKeyedArchiver", "$top": {"root": plistlib.UID(1)},
        "$objects": [
            "$null",
            {"NSRGB": ("%g %g %g" % (r, g, b)).encode() + b"\x00", "NSColorSpace": 2, "$class": plistlib.UID(2)},
            {"$classname": "NSColor", "$classes": ["NSColor", "NSObject"]},
        ],
    }
    return plistlib.dumps(arch, fmt=plistlib.FMT_BINARY)


def ns_font(name, size):
    arch = {
        "$version": 100000, "$archiver": "NSKeyedArchiver", "$top": {"root": plistlib.UID(1)},
        "$objects": [
            "$null",
            {"NSSize": float(size), "NSfFlags": 16, "NSName": plistlib.UID(2), "$class": plistlib.UID(3)},
            name,
            {"$classname": "NSFont", "$classes": ["NSFont", "NSObject"]},
        ],
    }
    return plistlib.dumps(arch, fmt=plistlib.FMT_BINARY)


def terminal_profile(v):
    bg, tx, ld = v["bg"], v["text"], v["lead"]
    dark = v["mode"] == "dark"
    sel = mix(bg["base"], ld["main"], 0.30 if dark else 0.22)
    p = {
        "name": v["name"], "type": "Window Settings", "ProfileCurrentVersion": 2.09,
        "BackgroundColor": ns_color(bg["base"]), "TextColor": ns_color(tx["fg"]),
        "TextBoldColor": ns_color(v["ansi"][15] if dark else tx["fg"]),
        "CursorColor": ns_color(ld["main"]), "SelectionColor": ns_color(sel),
        "Font": ns_font("SFMono-Regular", 13), "FontAntialias": True,
        "FontWidthSpacing": 1.0, "FontHeightSpacing": 1.1, "UseBrightBold": True,
        "BackgroundBlur": 0.0, "CursorBlink": True, "CursorType": 0, "Bell": False,
        "ShowActiveProcessInTitle": True, "ShowWindowSettingsNameInTitle": False,
        "columnCount": 120, "rowCount": 34, "useOptionAsMetaKey": True,
    }
    for i, n in enumerate(ANSI_NAMES):
        cap = n.capitalize()
        p["ANSI%sColor" % cap] = ns_color(v["ansi"][i])
        p["ANSIBright%sColor" % cap] = ns_color(v["ansi"][i + 8])
    return p


# ───────────────────────────── render / check ─────────────────────────────


def render(pal):
    out = {"zed/themes/orbitron.json": render_zed(pal)}
    for v in pal["variants"]:
        n = v["name"]
        out["xcode/%s.xccolortheme" % n] = plistlib.dumps(xcode_theme(v), fmt=plistlib.FMT_XML)
        out["xcode/%s.xcworkspacecolortheme" % n] = (json.dumps(xcode_workspace(v), indent=2) + "\n").encode()
        out["terminal/%s.terminal" % n] = plistlib.dumps(terminal_profile(v), fmt=plistlib.FMT_XML)
    out["VERSION"] = (pal["meta"]["version"] + "\n").encode()
    return out


def check(pal, out):
    problems = []
    rows = []

    def need(label, fgc, bgc, mn):
        c = contrast(fgc, bgc)
        if c < mn:
            problems.append("%-18s %-14s %s on %s = %.2f (< %.1f)" % (label[0], label[1], fgc, bgc, c, mn))
        return c

    for v in pal["variants"]:
        b = v["bg"]["base"]
        n = v["name"]
        need((n, "text"), v["text"]["fg"], b, 7.0)
        need((n, "muted"), v["text"]["muted"], b, 4.5)
        need((n, "placeholder"), v["text"]["placeholder"], b, 3.0)
        need((n, "lead"), v["lead"]["main"], b, 3.0)
        need((n, "lead.hi"), v["lead"]["hi"], b, 4.5)
        floors = {"cmt": 3.5, "doc": 4.0, "punct": 4.5}
        for k, c in v["syn"].items():
            need((n, "syn." + k), c, b, floors.get(k, 4.5))
        for k, c in v["status"].items():
            need((n, "status." + k), c, b, 4.5)
        for i, c in enumerate(v["ansi"]):
            if i == 0:
                continue
            need((n, "ansi[%d]" % i), c, b, 3.0 if i == 8 else 3.5)
        rows.append((n, contrast(v["text"]["fg"], b), contrast(v["lead"]["main"], b), contrast(v["syn"]["kw"], b)))

    # Zed key coverage
    required = set(ZED_KEYS.read_text().split())
    for t in json.loads(out["zed/themes/orbitron.json"])["themes"]:
        missing = required - set(t["style"])
        if missing:
            problems.append("%s: missing %d Zed keys: %s" % (t["name"], len(missing), " ".join(sorted(missing))))
        bad = [k for k, x in t["style"].items() if isinstance(x, str) and x.startswith("#") and len(x) not in (7, 9)]
        if bad:
            problems.append("%s: malformed colours: %s" % (t["name"], bad))

    # outputs up to date
    for rel, data in out.items():
        p = ROOT / rel
        if not p.exists() or p.read_bytes() != data:
            problems.append("stale or missing output: " + rel + "  (run scripts/build.py)")

    print("%-20s %8s %8s %10s" % ("variant", "text", "lead", "keyword"))
    for r in rows:
        print("%-20s %7.1f: %7.1f: %9.1f:" % r)
    n_keys = len(json.loads(out["zed/themes/orbitron.json"])["themes"][0]["style"])
    print("\nZed keys per theme: %d (required %d)" % (n_keys, len(required)))
    if problems:
        print("\n✖ %d problem(s):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("✔ all checks passed")
    return 0


def main():
    pal = json.loads(PALETTE.read_text())
    out = render(pal)
    if "--check" in sys.argv:
        sys.exit(check(pal, out))
    for rel, data in out.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        print("wrote", rel)
    # Zed key list is derived from the generated theme the first time, then maintained by hand
    if not ZED_KEYS.exists():
        keys = sorted(json.loads(out["zed/themes/orbitron.json"])["themes"][0]["style"])
        ZED_KEYS.write_text("\n".join(keys) + "\n")
        print("wrote scripts/zed_keys.txt")


if __name__ == "__main__":
    main()
