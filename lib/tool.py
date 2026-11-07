#!/usr/bin/env python3
"""Orbitron installer helper. Standard library only. Run with `python3 -I`.

Handles the fiddly, risk-bearing edits the shell scripts shouldn't:
  * Zed settings.json is JSONC (comments, trailing commas): edit ONLY the top-level
    "theme" value as text, validate, write atomically. File contents are never printed.
  * Claude Code theme (ANSI so it follows the terminal palette).
  * Terminal.app default profile (via `defaults`).
  * Install state (~/.orbitron/state.json) so uninstall can put everything back.

Exit codes: 0 changed/ok, 2 nothing to do, 1 error. One human-readable line on stdout.
"""
import argparse
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ───────────────────────────── JSONC scanning ─────────────────────────────


def _skip_ws(t, i):
    n = len(t)
    while i < n:
        if t[i] in " \t\r\n":
            i += 1
        elif t.startswith("//", i):
            j = t.find("\n", i)
            i = n if j < 0 else j + 1
        elif t.startswith("/*", i):
            j = t.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            break
    return i


def _str_end(t, i):
    """t[i] == '"'; return index just past the closing quote."""
    i += 1
    while i < len(t):
        if t[i] == "\\":
            i += 2
        elif t[i] == '"':
            return i + 1
        else:
            i += 1
    raise ValueError("unterminated string")


def _value_end(t, i):
    c = t[i]
    if c == '"':
        return _str_end(t, i)
    if c in "{[":
        depth = 0
        while i < len(t):
            c = t[i]
            if c == '"':
                i = _str_end(t, i)
                continue
            if t.startswith("//", i) or t.startswith("/*", i):
                i = _skip_ws(t, i)
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise ValueError("unbalanced brackets")
    while i < len(t) and t[i] not in ",}] \t\r\n/":
        i += 1
    return i


def root_members(t):
    """Return (root_open_index, {key: (key_start, val_start, val_end)}) for the top-level object."""
    i = _skip_ws(t, 0)
    if i >= len(t) or t[i] != "{":
        raise ValueError("settings root is not an object")
    root = i
    i += 1
    members = {}
    while True:
        i = _skip_ws(t, i)
        if i >= len(t):
            raise ValueError("unterminated root object")
        if t[i] == "}":
            return root, members
        if t[i] == ",":
            i += 1
            continue
        if t[i] != '"':
            raise ValueError("unexpected token in root object")
        ks = i
        ke = _str_end(t, i)
        key = json.loads(t[ks:ke])
        i = _skip_ws(t, ke)
        if t[i] != ":":
            raise ValueError("expected ':'")
        vs = _skip_ws(t, i + 1)
        ve = _value_end(t, vs)
        members[key] = (ks, vs, ve)
        i = ve


def strip_jsonc(t):
    """Comments and trailing commas out, string-aware, so json.loads can validate."""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == '"':
            j = _str_end(t, i)
            out.append(t[i:j])
            i = j
        elif t.startswith("//", i) or t.startswith("/*", i):
            i = _skip_ws(t, i)
        else:
            out.append(c)
            i += 1
    s = "".join(out)
    res, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = _str_end(s, i)
            res.append(s[i:j])
            i = j
        elif c == ",":
            k = i + 1
            while k < n and s[k] in " \t\r\n":
                k += 1
            if k < n and s[k] in "}]":
                i += 1
                continue
            res.append(c)
            i += 1
        else:
            res.append(c)
            i += 1
    return "".join(res)


def line_indent(t, idx):
    ls = t.rfind("\n", 0, idx) + 1
    seg = t[ls:idx]
    return seg if not seg.strip() else ""


def atomic_write(path, text, mode=None):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".orbitron-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    if mode is not None:
        os.chmod(tmp, mode)
    else:
        try:
            os.chmod(tmp, path.stat().st_mode & 0o777)
        except FileNotFoundError:
            pass
    os.replace(tmp, path)


# ───────────────────────────── state ─────────────────────────────


def load_state(p):
    try:
        return json.loads(Path(p).read_text())
    except (FileNotFoundError, ValueError):
        return {}


def save_state(p, st):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(p.parent, 0o700)
    atomic_write(p, json.dumps(st, indent=2) + "\n", 0o600)


def say(msg, code=0):
    print(msg)
    sys.exit(code)


# ───────────────────────────── Zed ─────────────────────────────


def new_theme_value(indent, light, dark):
    i2 = indent + "  "
    return '{\n%s"mode": "system",\n%s"light": %s,\n%s"dark": %s\n%s}' % (
        i2, i2, json.dumps(light), i2, json.dumps(dark), indent)


def zed_set_theme(text, value_builder):
    """Return new text with top-level "theme" replaced (or inserted)."""
    root, members = root_members(text)
    if "theme" in members:
        ks, vs, ve = members["theme"]
        old_raw = text[vs:ve]
        return text[:vs] + value_builder(line_indent(text, ks)) + text[ve:], old_raw
    indent = "  "
    ins = '\n%s"theme": %s%s' % (indent, value_builder(indent), "," if members else "\n")
    return text[:root + 1] + ins + text[root + 1:], None


def cmd_zed_apply(a):
    p = Path(a.settings)
    if not p.exists():
        say("no Zed settings.json yet (Zed will use the theme once selected)", 2)
    text = p.read_text()
    new, old_raw = zed_set_theme(text, lambda ind: new_theme_value(ind, a.light, a.dark))
    parsed = json.loads(strip_jsonc(new))
    if parsed.get("theme") != {"mode": "system", "light": a.light, "dark": a.dark}:
        say("validation failed; settings left untouched", 1)
    st = load_state(a.state)
    already = old_raw is not None and "Orbitron" in old_raw
    if not already:  # never overwrite the saved original with our own value
        st["zed"] = {"settings": str(p), "previous_theme_raw": old_raw}
    st.setdefault("zed", {"settings": str(p), "previous_theme_raw": None})
    if new == text:
        say("Zed theme already set (%s / %s)" % (a.light, a.dark), 2)
    if a.dry_run:
        say("would set Zed theme: light=%s dark=%s" % (a.light, a.dark))
    atomic_write(p, new)
    save_state(a.state, st)
    say("Zed theme set: light=%s dark=%s" % (a.light, a.dark))


def cmd_zed_restore(a):
    st = load_state(a.state)
    z = st.get("zed")
    p = Path(a.settings or (z or {}).get("settings", ""))
    if not z or not p.exists():
        say("no Zed theme change recorded", 2)
    text = p.read_text()
    root, members = root_members(text)
    if "theme" not in members or "Orbitron" not in text[members["theme"][1]:members["theme"][2]]:
        say("Zed theme was changed since install; leaving it alone", 2)
    prev = z.get("previous_theme_raw")
    if prev is None:
        prev = '{"mode": "system", "light": "One Light", "dark": "One Dark"}'
    new, _ = zed_set_theme(text, lambda ind: prev)
    json.loads(strip_jsonc(new))
    if a.dry_run:
        say("would restore previous Zed theme")
    atomic_write(p, new)
    st.pop("zed", None)
    save_state(a.state, st)
    say("Zed theme restored")


# ───────────────────────────── Claude Code ─────────────────────────────


def _claude_files(a):
    return [Path(a.settings), Path(a.claude_json)]


def cmd_claude_apply(a):
    st = load_state(a.state)
    changed, notes = {}, []
    for p in _claude_files(a):
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text())
        except ValueError:
            notes.append("%s is not plain JSON; skipped" % p.name)
            continue
        cur = d.get("theme")
        if cur in ("dark-ansi", "light-ansi"):
            notes.append("%s already ANSI (%s)" % (p.name, cur))
            continue
        if cur is None and p.name != "settings.json":
            continue  # only create the key in settings.json
        if a.dry_run:
            notes.append("would set %s theme to dark-ansi" % p.name)
            continue
        changed[str(p)] = cur
        d["theme"] = "dark-ansi"
        atomic_write(p, json.dumps(d, indent=2) + "\n")
        notes.append("%s theme -> dark-ansi" % p.name)
    if changed:
        st.setdefault("claude", {}).update(changed)
        save_state(a.state, st)
    say("; ".join(notes) if notes else "Claude Code config not found",
        0 if changed or any(n.startswith("would") for n in notes) else 2)


def cmd_claude_restore(a):
    st = load_state(a.state)
    c = st.get("claude")
    if not c:
        say("no Claude Code change recorded", 2)
    for path, prev in c.items():
        p = Path(path)
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        if d.get("theme") != "dark-ansi":
            continue
        if a.dry_run:
            continue
        if prev is None:
            d.pop("theme", None)
        else:
            d["theme"] = prev
        atomic_write(p, json.dumps(d, indent=2) + "\n")
    if not a.dry_run:
        st.pop("claude", None)
        save_state(a.state, st)
    say("Claude Code theme restored" if not a.dry_run else "would restore Claude Code theme")


# ───────────────────────────── Terminal.app ─────────────────────────────


def _defaults_read(key):
    r = subprocess.run(["defaults", "read", "com.apple.Terminal", key], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def cmd_terminal_apply(a):
    st = load_state(a.state)
    prev = {k: _defaults_read(k) for k in ("Default Window Settings", "Startup Window Settings")}
    if prev["Default Window Settings"] == a.profile:
        say("Terminal.app default already %s" % a.profile, 2)
    if a.dry_run:
        say("would set Terminal.app default profile to %s" % a.profile)
    st["terminal"] = {"previous": prev, "profile": a.profile}
    for k in prev:
        subprocess.run(["defaults", "write", "com.apple.Terminal", k, "-string", a.profile], check=True)
    save_state(a.state, st)
    say("Terminal.app default profile: %s (restart Terminal to apply)" % a.profile)


def cmd_terminal_restore(a):
    st = load_state(a.state)
    t = st.get("terminal")
    if not t:
        say("no Terminal.app default change recorded", 2)
    cur = _defaults_read("Default Window Settings") or ""
    if a.dry_run:
        say("would restore Terminal.app default profile")
    if cur.startswith("Orbitron"):
        for k, v in t["previous"].items():
            if v:
                subprocess.run(["defaults", "write", "com.apple.Terminal", k, "-string", v], check=True)
            else:
                subprocess.run(["defaults", "delete", "com.apple.Terminal", k], capture_output=True)
    st.pop("terminal", None)
    save_state(a.state, st)
    say("Terminal.app default profile restored")


def cmd_terminal_remove(a):
    """Delete imported Orbitron* profiles from Terminal.app's preferences. Terminal must be closed."""
    r = subprocess.run(["defaults", "export", "com.apple.Terminal", "-"], capture_output=True)
    if r.returncode != 0:
        say("Terminal.app preferences not found", 2)
    d = plistlib.loads(r.stdout)
    ws = d.get("Window Settings", {})
    gone = [k for k in ws if k.startswith("Orbitron")]
    if not gone:
        say("no Orbitron profiles in Terminal.app", 2)
    if a.dry_run:
        say("would remove %d Terminal.app profile(s)" % len(gone))
    for k in gone:
        del ws[k]
    subprocess.run(["defaults", "import", "com.apple.Terminal", "-"], input=plistlib.dumps(d), check=True)
    say("removed %d Terminal.app profile(s)" % len(gone))


# ───────────────────────────── state & palette ─────────────────────────────


def cmd_state_files(a):
    st = load_state(a.state)
    files = set(st.get("files", []))
    files.update(a.paths)
    st["files"] = sorted(files)
    st["version"] = a.version
    st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    st.setdefault("installed_at", st["updated_at"])
    save_state(a.state, st)
    say("state saved")


def cmd_state_get(a):
    st = load_state(a.state)
    cur = st
    for part in a.key.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    if isinstance(cur, list):
        print("\n".join(cur))
    elif cur is not None:
        print(cur)
    sys.exit(0 if cur is not None else 2)


def cmd_state_clear(a):
    try:
        os.remove(a.state)
    except FileNotFoundError:
        pass
    say("state cleared")


def cmd_swatches(a):
    pal = json.loads(Path(a.palette).read_text())
    for v in pal["variants"]:
        ansi = v["ansi"]
        cols = [v["bg"]["base"], v["lead"]["main"], ansi[5], ansi[6], ansi[4], ansi[2], ansi[3], ansi[1], v["syn"]["ty"]]
        print("|".join([v["id"], v["name"], v["mode"], v["tagline"], ",".join(c.lstrip("#") for c in cols)]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args, **flags):
        sp = sub.add_parser(name)
        for a in args:
            sp.add_argument(a, required=True)
        sp.add_argument("--dry-run", action="store_true")
        sp.set_defaults(fn=fn)
        return sp

    s = add("zed-apply", cmd_zed_apply, "--settings", "--light", "--dark", "--state")
    s = add("zed-restore", cmd_zed_restore, "--state")
    s.add_argument("--settings")
    add("claude-apply", cmd_claude_apply, "--settings", "--claude-json", "--state")
    add("claude-restore", cmd_claude_restore, "--state")
    add("terminal-apply", cmd_terminal_apply, "--profile", "--state")
    add("terminal-restore", cmd_terminal_restore, "--state")
    add("terminal-remove", cmd_terminal_remove)
    s = add("state-files", cmd_state_files, "--state", "--version")
    s.add_argument("paths", nargs="*")
    s = add("state-get", cmd_state_get, "--state", "--key")
    add("state-clear", cmd_state_clear, "--state")
    add("swatches", cmd_swatches, "--palette")
    a = ap.parse_args()
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:  # never leak file contents; message only
        say("error: %s: %s" % (type(e).__name__, e), 1)


if __name__ == "__main__":
    main()
