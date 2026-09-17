"""Pacotes de ícones para a interface do app (integrados ou importados pelo usuário).

Um pacote define um glifo (emoji/símbolo) ou um PNG para cada chave de ícone:
home, mouse, click, trail, font, icons, settings, theme, apply, download, close.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from . import paths

KEYS = ["home", "mouse", "click", "trail", "font", "icons", "settings", "theme"]

BUILTIN: dict[str, dict[str, str]] = {
    "Neon Padrão": {
        "home": "🏠", "mouse": "🖱️", "click": "✨", "trail": "🌈", "font": "🔤",
        "icons": "🎨", "settings": "⚙️", "theme": "🌗", "apply": "✅", "download": "⬇️",
        "close": "✕",
    },
    "Minimal": {
        "home": "⌂", "mouse": "➤", "click": "✦", "trail": "⌇", "font": "A",
        "icons": "▤", "settings": "⚙", "theme": "◐", "apply": "✔", "download": "↓",
        "close": "×",
    },
    "Pastel Sonho": {
        "home": "🏡", "mouse": "🌟", "click": "💥", "trail": "💫", "font": "📖",
        "icons": "🖼️", "settings": "🛠️", "theme": "🌙", "apply": "⭐", "download": "📥",
        "close": "❌",
    },
    "Cyber": {
        "home": "🟩", "mouse": "🕹️", "click": "⚡", "trail": "🔷", "font": "🅰️",
        "icons": "🧩", "settings": "🔧", "theme": "🔮", "apply": "🟢", "download": "📀",
        "close": "⛔",
    },
}


def _user_dir() -> Path:
    return paths.icon_packs_dir()


def list_packs() -> dict[str, dict]:
    """{nome: {"glyphs": {chave: glifo}, "pngs": {chave: caminho}}}"""
    out: dict[str, dict] = {}
    for name, glyphs in BUILTIN.items():
        out[name] = {"glyphs": dict(glyphs), "pngs": {}}
    d = _user_dir()
    if d.exists():
        for folder in sorted(d.iterdir()):
            if not folder.is_dir():
                continue
            glyphs, pngs = {}, {}
            try:
                pj = folder / "pack.json"
                if pj.exists():
                    meta = json.loads(pj.read_text("utf-8"))
                    name = meta.get("name", folder.name)
                    glyphs.update(meta.get("glyphs", {}))
                else:
                    name = folder.name
            except Exception:
                name = folder.name
            for f in folder.glob("*.png"):
                key = f.stem.lower()
                if key in KEYS or key in ("apply", "download", "close"):
                    pngs[key] = str(f)
            if glyphs or pngs:
                out[name] = {"glyphs": glyphs, "pngs": pngs}
    return out


def get_active() -> dict:
    packs = list_packs()
    name = "Neon Padrão"
    from . import config
    saved = config.get("theme.icon_pack", "Neon Padrão")
    if saved in packs:
        name = saved
    return {"name": name, **packs[name]}


def glyph(key: str, fallback: str = "•") -> str:
    active = get_active()
    return active["glyphs"].get(key, fallback)


def png_for(key: str) -> str | None:
    return get_active()["pngs"].get(key)


def import_zip(zip_path) -> str | None:
    """Importa um pacote de ícones (.zip com pack.json e/ou pngs nomeados)."""
    zip_path = Path(zip_path)
    d = _user_dir()
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f"_tmp_{zip_path.stem}"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)
    folder = next((p for p in tmp.iterdir() if p.is_dir()), tmp)
    glyphs, pngs = {}, {}
    try:
        pj = folder / "pack.json"
        if pj.exists():
            meta = json.loads(pj.read_text("utf-8"))
            glyphs.update(meta.get("glyphs", {}))
    except Exception:
        pass
    for f in folder.glob("*.png"):
        key = f.stem.lower()
        if key in KEYS or key in ("apply", "download", "close"):
            pngs[key] = str(f)
    if not glyphs and not pngs:
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    name = glyphs.get("name") or folder.name or zip_path.stem
    dest = d / "".join(c if (c.isalnum() or c in " -_()") else "_" for c in name)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.move(str(folder), str(dest))
    try:
        meta = {"name": name, "glyphs": glyphs}
        (dest / "pack.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    except Exception:
        pass
    shutil.rmtree(tmp, ignore_errors=True)
    if pngs:
        for k, src in pngs.items():
            try:
                shutil.copy2(src, dest / f"{k}.png")
            except Exception:
                pass
    return name


def import_dir(src) -> str | None:
    src = Path(src)
    pngs = {f.stem.lower(): str(f) for f in src.glob("*.png")
            if f.stem.lower() in KEYS or f.stem.lower() in ("apply", "download", "close")}
    glyphs = {}
    try:
        pj = src / "pack.json"
        if pj.exists():
            glyphs = json.loads(pj.read_text("utf-8")).get("glyphs", {})
    except Exception:
        pass
    if not glyphs and not pngs:
        return None
    name = src.name
    dest = _user_dir() / "".join(c if (c.isalnum() or c in " -_()") else "_" for c in name)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)
    try:
        meta = {"name": name, "glyphs": glyphs}
        (dest / "pack.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    except Exception:
        pass
    return name
