"""Orbitron icon themes for Zed. Imported by build.py; standard library only.

Design: 16px "chips" and folders drawn with a 1.25px rounded stroke and a soft 14% tint.
Languages get a tiny stroke-font monogram (no <text>, so nothing depends on installed fonts);
everything else gets a pictogram. Folders carry the same pictograms as badges.
Colours come from each variant's palette, so icons always match the editor theme.
"""
import json

# ───────────────────────────── stroke font (3 wide × 5 tall) ─────────────────────────────
# polylines "x,y x,y …" separated by ";"; trailing "z" closes the line.
_FONT = {
    "A": "0,5 1.5,0 3,5;0.6,3.4 2.4,3.4", "B": "0,0 0,5 2,5 3,4 3,3 2,2.5 0,2.5;0,0 2,0 3,1 3,1.8 2,2.5",
    "C": "3,1 2,0 1,0 0,1 0,4 1,5 2,5 3,4", "D": "0,0 0,5 1.8,5 3,4 3,1 1.8,0 z",
    "E": "3,0 0,0 0,5 3,5;0,2.5 2.2,2.5", "F": "3,0 0,0 0,5;0,2.5 2.2,2.5",
    "G": "3,1 2,0 1,0 0,1 0,4 1,5 2,5 3,4 3,2.7 1.6,2.7", "H": "0,0 0,5;3,0 3,5;0,2.5 3,2.5",
    "I": "0.5,0 2.5,0;1.5,0 1.5,5;0.5,5 2.5,5", "J": "3,0 3,4 2,5 1,5 0,4", "K": "0,0 0,5;3,0 0,3;1,2.3 3,5",
    "L": "0,0 0,5 3,5", "M": "0,5 0,0 1.5,2.5 3,0 3,5", "N": "0,5 0,0 3,5 3,0",
    "O": "1,0 2,0 3,1 3,4 2,5 1,5 0,4 0,1 z", "P": "0,5 0,0 2,0 3,1 3,2 2,3 0,3",
    "Q": "1,0 2,0 3,1 3,4 2,5 1,5 0,4 0,1 z;2,3.6 3,5", "R": "0,5 0,0 2,0 3,1 3,2 2,3 0,3;1.6,3 3,5",
    "S": "3,1 2,0 1,0 0,1 0,1.7 1,2.5 2,2.5 3,3.3 3,4 2,5 1,5 0,4", "T": "0,0 3,0;1.5,0 1.5,5",
    "U": "0,0 0,4 1,5 2,5 3,4 3,0", "V": "0,0 1.5,5 3,0", "W": "0,0 0.8,5 1.5,2.5 2.2,5 3,0",
    "X": "0,0 3,5;3,0 0,5", "Y": "0,0 1.5,2.5 3,0;1.5,2.5 1.5,5", "Z": "0,0 3,0 0,5 3,5",
    "+": "1.5,1.4 1.5,3.6;0.4,2.5 2.6,2.5", "#": "1,0 0.6,5;2.4,0 2,5;0,1.7 3,1.7;0,3.3 3,3.3",
}


def mono(text, w=12.0, x0=2.0, y0=2.0, h=12.0):
    """Stroke-font monogram centred in the chip box; returns one <path/>."""
    n = len(text)
    s = 1.55 if n == 1 else 1.12
    gap = 0 if n == 1 else 1.1
    total = n * 3 * s + (n - 1) * gap
    ox = x0 + (w - total) / 2
    oy = y0 + (h - 5 * s) / 2
    d = []
    for i, ch in enumerate(text):
        lx = ox + i * (3 * s + gap)
        for line in _FONT[ch].split(";"):
            pts = line.split()
            closed = pts[-1] == "z"
            pts = [p for p in pts if p != "z"]
            seg = []
            for j, p in enumerate(pts):
                x, y = (float(v) for v in p.split(","))
                seg.append("%s%.2f %.2f" % ("M" if j == 0 else "L", lx + x * s, oy + y * s))
            d.append("".join(seg) + ("Z" if closed else ""))
    return '<path d="%s" stroke-width="1.15"/>' % "".join(d)


# ───────────────────────────── pictograms (16-unit grid, stroke only) ─────────────────────────────
P = lambda d: '<path d="%s"/>' % d
GLYPH = {
    "code": P("M6.2 5.5 3.8 8l2.4 2.5M9.8 5.5 12.2 8l-2.4 2.5"),
    "html": P("M6 5.5 3.8 8 6 10.5M10 5.5 12.2 8 10 10.5M8.9 4.5 7.1 11.5"),
    "shell": P("m4.5 5.5 3 2.5-3 2.5M8.5 11h3.5"),
    "braces": P("M6.6 4c-1.3 0-1.6.8-1.6 1.7v.9c0 .9-.4 1.4-1 1.4.6 0 1 .5 1 1.4v.9c0 .9.3 1.7 1.6 1.7M9.4 4c1.3 0 1.6.8 1.6 1.7v.9c0 .9.4 1.4 1 1.4-.6 0-1 .5-1 1.4v.9c0 .9-.3 1.7-1.6 1.7"),
    "brackets": P("M6 4H4.6v8H6M10 4h1.4v8H10"),
    "list": P("M4.5 5.2h.01M7 5.2h5M4.5 8h.01M7 8h5M4.5 10.8h.01M7 10.8h5"),
    "lines": P("M4.5 5h7M4.5 8h7M4.5 11h4"),
    "doc": P("M5 4.5h6M5 7h6M5 9.5h6M5 12h3.5"),
    "markdown": P("M3.4 11V5l2.3 2.7L8 5v6M11 5v4.6M9.2 8.2l1.8 1.9 1.8-1.9"),
    "gear": P("M8 6.3a1.7 1.7 0 1 0 0 3.4 1.7 1.7 0 1 0 0-3.4ZM8 3.8v1.2M8 11v1.2M3.8 8H5M11 8h1.2M5 5l.9.9M10.1 10.1l.9.9M5 11l.9-.9M10.1 5.9l.9-.9"),
    "sliders": P("M4 5.5h8M4 8h8M4 10.5h8M6.2 4.3v2.4M10 6.8v2.4M7 9.3v2.4"),
    "lock": P("M5 7.5h6v4.5H5ZM6.2 7.5V6.2a1.8 1.8 0 0 1 3.6 0v1.3"),
    "shield": P("M8 3.5 12 5v3c0 2-1.7 3.4-4 4.4C5.7 11.4 4 10 4 8V5ZM6.2 8l1.3 1.3 2.3-2.5"),
    "image": P("M3.5 4.5h9v7h-9ZM3.8 10.8l2.7-3 2 2 1.6-1.6 2.3 2.4M10.2 6.5h.01"),
    "audio": P("M6.5 11.2V5.4l5-1.1v5.7M6.5 11.2a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0ZM11.5 10a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z"),
    "video": P("M3.5 5.2h7v5.6h-7ZM10.5 7.6 12.5 6v4l-2-1.6"),
    "archive": P("M3.5 4.5h9v2.2h-9ZM4.5 6.7v5.3h7V6.7M6.7 9h2.6"),
    "database": P("M4 5.4c0-.9 1.8-1.6 4-1.6s4 .7 4 1.6-1.8 1.6-4 1.6-4-.7-4-1.6ZM4 5.4v5.2c0 .9 1.8 1.6 4 1.6s4-.7 4-1.6V5.4M4 8c0 .9 1.8 1.6 4 1.6S12 8.9 12 8"),
    "git": P("M5.5 4.2v7.6M5.5 9.4c0-2 5-1.2 5-3.8") + '<circle cx="5.5" cy="4.2" r="1.1"/><circle cx="5.5" cy="11.8" r="1.1"/><circle cx="10.5" cy="5.4" r="1.1"/>',
    "docker": P("M3.2 8.4h9.6c.1 1.8-1.5 3.6-4.6 3.6-2.5 0-4.4-1-5-3.6ZM4.8 6.4h1.5v2H4.8ZM6.6 6.4h1.5v2H6.6ZM8.4 6.4h1.5v2H8.4ZM6.6 4.6h1.5v1.8H6.6Z"),
    "package": P("M8 3.5 12.3 6v4.2L8 12.5 3.7 10.2V6ZM8 3.5v4.4M3.7 6 8 7.9 12.3 6"),
    "test": P("M6.6 3.8h2.8M7.2 3.8v3.1L4.6 11.2c-.4.8.1 1.4.9 1.4h5c.8 0 1.3-.6.9-1.4L8.8 6.9V3.8M5.8 9.6h4.4"),
    "star": P("m8 3.6 1.3 2.9 3.1.4-2.3 2.1.6 3.1L8 10.5l-2.7 1.6.6-3.1-2.3-2.1 3.1-.4Z"),
    "link": P("M7 9.2a2.1 2.1 0 0 0 3 0l1.8-1.8a2.1 2.1 0 0 0-3-3l-.6.6M9 6.8a2.1 2.1 0 0 0-3 0L4.2 8.6a2.1 2.1 0 0 0 3 3l.6-.6"),
    "bolt": P("M8.8 3.5 4.6 8.8h3.2l-.7 3.7 4.3-5.3H8.2Z"),
    "cloud": P("M5.2 11.5a2.4 2.4 0 0 1-.4-4.8 3.4 3.4 0 0 1 6.5.8 2.1 2.1 0 0 1-.4 4Z"),
    "license": P("M8 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM9.6 9.3a2 2 0 1 1 0-2.6"),
    "font": P("M3.8 11.5 6.1 4.6l2.3 6.9M4.7 9.4h2.9M10.4 8.2c-1.3 0-2 .6-2 1.5 0 .8.6 1.3 1.4 1.3 1 0 1.6-.6 1.6-1.4V8.2c0-1-.5-1.5-1.5-1.5"),
    "graphql": P("M8 3.6l3.8 2.2v4.4L8 12.4l-3.8-2.2V5.8Z") + '<circle cx="8" cy="3.6" r=".6"/><circle cx="8" cy="12.4" r=".6"/>',
    "terraform": P("M4.3 4.4 7.4 6.2v3.5L4.3 7.9ZM8.2 6.2l3.1-1.8v3.5L8.2 9.7ZM8.2 10.4l3.1-1.8v3.5l-3.1 1.8Z"),
    "cube": P("M8 3.5 12.3 6v4.2L8 12.5 3.7 10.2V6ZM8 8v4.5M3.7 6 8 8l4.3-2"),
    "grid": P("M4.2 4.2h3.2v3.2H4.2ZM8.6 4.2h3.2v3.2H8.6ZM4.2 8.6h3.2v3.2H4.2ZM8.6 8.6h3.2v3.2H8.6Z"),
    "route": P("M4.5 11.5h4.2a2 2 0 0 0 0-4H7.3a2 2 0 0 1 0-4h4.2M4.5 11.5h.01M11.5 3.5h.01"),
    "api": P("M4 6h8M10 4l2 2-2 2M12 10H4M6 8l-2 2 2 2"),
    "hook": P("M8 3.6v5.6a2.4 2.4 0 1 1-2.4-2.4"),
    "lib": P("M4.6 4v8M7.2 4v8M9.8 5l2.4 7"),
    "spark": P("M8 3.5 9.2 6.8 12.5 8 9.2 9.2 8 12.5 6.8 9.2 3.5 8 6.8 6.8Z"),
    "clock": P("M8 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM8 6v2.2l1.5 1"),
    "orbit": '<ellipse cx="8" cy="8" rx="4.6" ry="2.1" transform="rotate(-30 8 8)"/><circle cx="8" cy="8" r="1.1"/>',
    "react": '<ellipse cx="8" cy="8" rx="4.6" ry="1.9"/><ellipse cx="8" cy="8" rx="4.6" ry="1.9" transform="rotate(60 8 8)"/><ellipse cx="8" cy="8" rx="4.6" ry="1.9" transform="rotate(120 8 8)"/><circle cx="8" cy="8" r=".7"/>',
    "text": P("M4.5 5h7M8 5v6.5M6.5 11.5h3"),
    "cube3": P("M8 3.5 12 5.8v4.4L8 12.5 4 10.2V5.8Z"),
}

# ───────────────────────────── file icon table ─────────────────────────────
# id: (role, kind, payload)   kind "m" = monogram text, "g" = pictogram name
FILES = {
    "default": ("muted", "g", "doc"), "document": ("muted", "g", "lines"), "text": ("muted", "g", "text"),
    "typescript": ("fn", "m", "TS"), "javascript": ("num", "m", "JS"), "react": ("fn", "g", "react"),
    "rust": ("rx", "m", "RS"), "swift": ("param", "m", "SW"), "python": ("prop", "m", "PY"),
    "go": ("fn", "m", "GO"), "ruby": ("err", "m", "RB"), "java": ("rx", "m", "J"), "kotlin": ("ty", "m", "KT"),
    "c": ("prop", "m", "C"), "cpp": ("prop", "m", "C+"), "csharp": ("ty", "m", "C#"), "php": ("ty", "m", "PH"),
    "vue": ("str", "m", "V"), "svelte": ("rx", "m", "SV"), "astro": ("hi", "m", "A"),
    "lua": ("prop", "m", "LU"), "zig": ("num", "m", "ZG"), "elixir": ("ty", "m", "EX"), "haskell": ("ty", "m", "HS"),
    "dart": ("fn", "m", "DT"), "scala": ("err", "m", "SC"), "nix": ("prop", "m", "NX"), "wasm": ("ty", "m", "WA"),
    "html": ("rx", "g", "html"), "css": ("prop", "m", "#"), "sass": ("kw", "m", "S"),
    "json": ("num", "g", "braces"), "yaml": ("param", "g", "list"), "toml": ("rx", "g", "brackets"),
    "xml": ("str", "g", "code"), "markdown": ("fn", "g", "markdown"), "shell": ("str", "g", "shell"),
    "database": ("ty", "g", "database"), "docker": ("prop", "g", "docker"), "git": ("rx", "g", "git"),
    "lock": ("muted", "g", "lock"), "package": ("hi", "g", "package"), "settings": ("special", "g", "gear"),
    "config": ("special", "g", "sliders"), "shield": ("str", "g", "shield"), "test": ("str", "g", "test"),
    "star": ("hi", "g", "star"), "license": ("num", "g", "license"), "log": ("faint", "g", "lines"),
    "image": ("ty", "g", "image"), "audio": ("kw", "g", "audio"), "video": ("kw", "g", "video"),
    "archive": ("num", "g", "archive"), "font": ("kw", "g", "font"), "graphql": ("kw", "g", "graphql"),
    "terraform": ("ty", "g", "terraform"), "cloud": ("fn", "g", "cloud"), "bolt": ("num", "g", "bolt"),
    "link": ("fn", "g", "link"), "data": ("str", "g", "list"), "code": ("fn", "g", "code"), "types": ("ty", "m", "T"),
}

SUFFIXES = {
    "typescript": "ts mts cts", "javascript": "js mjs cjs jsm", "react": "tsx jsx", "rust": "rs", "swift": "swift",
    "python": "py pyi pyw ipynb", "go": "go", "ruby": "rb rake gemspec erb", "java": "java jar gradle", "kotlin": "kt kts",
    "c": "c h", "cpp": "cpp cc cxx hpp hxx hh", "csharp": "cs csx csproj", "php": "php phtml", "vue": "vue",
    "svelte": "svelte", "astro": "astro", "lua": "lua", "zig": "zig", "elixir": "ex exs", "haskell": "hs lhs",
    "dart": "dart", "scala": "scala sbt", "nix": "nix", "wasm": "wasm wat", "html": "html htm xhtml",
    "css": "css pcss postcss", "sass": "scss sass less styl", "json": "json jsonc json5 jsonl",
    "yaml": "yml yaml", "toml": "toml", "xml": "xml plist xib storyboard xcconfig", "markdown": "md mdx markdown",
    "shell": "sh bash zsh fish ps1 command", "database": "sql sqlite db prisma", "docker": "dockerfile",
    "git": "gitignore gitattributes", "lock": "lock", "settings": "ini cfg conf env editorconfig",
    "config": "properties rc", "test": "spec test snap", "license": "license", "log": "log out",
    "image": "png jpg jpeg gif webp avif ico icns bmp svg tiff heic", "audio": "mp3 wav aac flac ogg m4a aiff",
    "video": "mp4 mov mkv webm avi m4v", "archive": "zip tar gz tgz rar 7z bz2 xz dmg pkg",
    "font": "ttf otf woff woff2 eot", "graphql": "graphql gql", "terraform": "tf tfvars hcl",
    "data": "csv tsv parquet ndjson", "text": "txt rtf", "document": "pdf doc docx pages", "types": "d.ts",
    "link": "webloc url",
}

STEMS = {
    "package": "package.json", "lock": "package-lock.json pnpm-lock.yaml yarn.lock bun.lock bun.lockb Cargo.lock go.sum Gemfile.lock Podfile.lock composer.lock poetry.lock Package.resolved",
    "rust": "Cargo.toml", "go": "go.mod", "ruby": "Gemfile Rakefile", "swift": "Package.swift Podfile",
    "docker": "Dockerfile Containerfile .dockerignore docker-compose.yml docker-compose.yaml compose.yml compose.yaml",
    "shield": ".env .env.local .env.example .env.production .env.development .env.test",
    "git": ".gitignore .gitattributes .gitmodules .gitkeep", "settings": ".editorconfig .prettierrc .prettierignore .npmrc .nvmrc .node-version",
    "typescript": "tsconfig.json", "javascript": "jsconfig.json", "bolt": "vite.config.ts vite.config.js vite.config.mjs",
    "test": "vitest.config.ts playwright.config.ts jest.config.js jest.config.ts", "config": "eslint.config.js eslint.config.mjs .eslintrc.json .eslintrc.js tailwind.config.js tailwind.config.ts postcss.config.js next.config.js next.config.mjs",
    "cloud": "wrangler.toml wrangler.json wrangler.jsonc vercel.json netlify.toml fly.toml",
    "markdown": "README.md CHANGELOG.md CONTRIBUTING.md", "star": "AGENTS.md CLAUDE.md",
    "license": "LICENSE LICENSE.md LICENSE.txt LICENCE COPYING", "shell": "Makefile Justfile .zshrc .bashrc .zprofile .bash_profile",
}

# folder categories: role, pictogram, names
FOLDERS = {
    "src": ("kw", "code", "src source sources app apps core"),
    "components": ("fn", "grid", "components ui widgets views"),
    "routes": ("ty", "route", "routes pages screens navigation"),
    "api": ("fn", "api", "api server services endpoints controllers"),
    "hooks": ("ty", "hook", "hooks composables"),
    "lib": ("prop", "lib", "lib libs shared common utils utilities helpers"),
    "styles": ("kw", "spark", "styles style css scss sass stylesheets themes"),
    "assets": ("ty", "image", "assets images img media icons fonts public static"),
    "config": ("special", "sliders", "config configs .config settings"),
    "build": ("num", "cube", "build dist out target .next .output release bin"),
    "cache": ("faint", "clock", ".cache cache tmp temp .tmp"),
    "database": ("ty", "database", "db database data migrations schema models prisma supabase"),
    "docker": ("prop", "docker", "docker .docker containers"),
    "docs": ("fn", "doc", "docs doc documentation"),
    "git": ("rx", "git", ".git .github .gitlab"),
    "tests": ("str", "test", "test tests __tests__ spec specs e2e"),
    "scripts": ("str", "shell", "scripts script tools tooling"),
    "security": ("str", "shield", "auth security secrets"),
    "state": ("hi", "orbit", "state store stores redux context"),
    "types": ("ty", "braces", "types typings @types interfaces"),
    "packages": ("num", "package", "packages node_modules vendor"),
    "features": ("hi", "star", "features modules plugins"),
    "cloud": ("fn", "cloud", "cloud aws terraform .terraform infra"),
}

FOLDER_CLOSED = "M2.75 3.25h3l1.4 1.75h6.1c.5 0 .75.25.75.75v6.5c0 .5-.25.75-.75.75H2.75c-.5 0-.75-.25-.75-.75V4c0-.5.25-.75.75-.75Z"
FOLDER_BACK = "M2 12.4V4c0-.5.25-.75.75-.75h3l1.4 1.75h5.1c.5 0 .75.25.75.75V7"
FOLDER_FRONT = "M1.75 12.4 3.2 7.6a.9.9 0 0 1 .87-.65h9.7a.75.75 0 0 1 .72.95l-1.3 4.6a.9.9 0 0 1-.87.65H2.5a.75.75 0 0 1-.75-.75Z"


def _svg(inner):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">%s</svg>\n' % inner


def _g(color, inner, extra=""):
    return ('<g fill="none" stroke="%s" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"%s>%s</g>'
            % (color, extra, inner))


def roles(v):
    tx, sy, st, ld = v["text"], v["syn"], v["status"], v["lead"]
    return {
        "kw": sy["kw"], "fn": sy["fn"], "ty": sy["ty"], "str": sy["str"], "num": sy["num"], "prop": sy["prop"],
        "param": sy["param"], "rx": sy["rx"], "special": sy["special"], "err": st["error"],
        "hi": ld["hi"] if v["mode"] == "dark" else ld["main"], "muted": tx["muted"], "faint": tx["placeholder"],
        "lead": ld["main"],
    }


def file_icon(color, kind, payload):
    body = mono(payload) if kind == "m" else GLYPH[payload]
    chip = '<rect x="2" y="2" width="12" height="12" rx="3.5" fill="%s" fill-opacity="0.14"/>' % color
    if kind == "g":
        # pictograms are drawn on the 16 grid: shrink slightly so they sit inside the chip
        body = '<g transform="translate(8 8) scale(.86) translate(-8 -8)" stroke-width="1.45">%s</g>' % body
    return _svg(_g(color, chip + body))


def folder_icon(color, glyph=None, open_=False):
    badge = ""
    if glyph:
        # glyph centred in the folder body (8, 9.6) at 55%
        badge = '<g transform="translate(%.2f %.2f) scale(.55)" stroke-width="2">%s</g>' % (8 - 8 * .55, (10.0 if open_ else 9.4) - 8 * .55, GLYPH[glyph])
    if open_:
        inner = ('<path d="%s"/><path d="%s" fill="%s" fill-opacity="0.16"/>' % (FOLDER_BACK, FOLDER_FRONT, color)) + badge
    else:
        inner = '<path d="%s" fill="%s" fill-opacity="0.14"/>' % (FOLDER_CLOSED, color) + badge
    return _svg(_g(color, inner))


def chevron(color, down):
    return _svg(_g(color, P("m4 6 4 4 4-4") if down else P("m6 4 4 4-4 4")))


def build_variant(v):
    """-> {filename: svg text} for one variant."""
    r = roles(v)
    out = {}
    for fid, (role, kind, payload) in FILES.items():
        out[fid + ".svg"] = file_icon(r[role], kind, payload)
    out["folder.svg"] = folder_icon(r["lead"])
    out["folder-open.svg"] = folder_icon(r["lead"], open_=True)
    for cat, (role, glyph, _) in FOLDERS.items():
        out["folder-%s.svg" % cat] = folder_icon(r[role], glyph)
        out["folder-%s-open.svg" % cat] = folder_icon(r[role], glyph, open_=True)
    out["chevron-right.svg"] = chevron(r["muted"], False)
    out["chevron-down.svg"] = chevron(r["muted"], True)
    return out


def icon_theme(v, slug):
    base = "./icons/%s/" % slug
    suffixes, stems = {}, {}
    for fid, text in SUFFIXES.items():
        for s in text.split():
            suffixes[s] = fid
    for fid, text in STEMS.items():
        for s in text.split():
            stems[s] = fid
    # stems may reference ids that only exist as icons (bolt, cloud, ...) — all are in FILES
    named = {}
    for cat, (_, _, names) in FOLDERS.items():
        for n in names.split():
            named[n] = {"collapsed": base + "folder-%s.svg" % cat, "expanded": base + "folder-%s-open.svg" % cat}
    return {
        "name": v["name"] + " Icons",
        "appearance": v["mode"],
        "directory_icons": {"collapsed": base + "folder.svg", "expanded": base + "folder-open.svg"},
        "named_directory_icons": named,
        "chevron_icons": {"collapsed": base + "chevron-right.svg", "expanded": base + "chevron-down.svg"},
        "file_stems": stems,
        "file_suffixes": suffixes,
        "file_icons": {fid: {"path": base + fid + ".svg"} for fid in FILES},
    }


EXT_TOML = '''id = "orbitron-icons"
name = "Orbitron Icons"
version = "{version}"
schema_version = 1
authors = ["{author}"]
description = "Original 16px file and folder icons for the Orbitron suite: stroke-font monograms and pictograms in each variant's palette."
repository = "{homepage}"
'''


def render(pal):
    """-> {repo-relative path: bytes} for the whole Zed icon extension."""
    out = {}
    meta = pal["meta"]
    themes = []
    for v in pal["variants"]:
        slug = v["id"]
        for name, text in build_variant(v).items():
            out["zed/extension/icons/%s/%s" % (slug, name)] = text.encode()
        themes.append(icon_theme(v, slug))
    doc = {"$schema": "https://zed.dev/schema/icon_themes/v0.3.0.json", "name": "Orbitron Icons",
           "author": meta["author"], "themes": themes}
    out["zed/extension/icon_themes/orbitron-icons.json"] = (json.dumps(doc, indent=2) + "\n").encode()
    out["zed/extension/extension.toml"] = EXT_TOML.format(
        version=meta["version"], author=meta["author"], homepage=meta["homepage"]).encode()
    return out
