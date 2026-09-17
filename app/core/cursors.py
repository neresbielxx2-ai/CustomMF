"""Gerenciamento de pacotes de cursor do Windows.

Suporta qualquer pacote .zip com install.inf (macOS, Bibata, BreezeX etc.),
importação manual, cursor feito a partir de uma imagem do usuário, backup e
restauração dos cursores — tudo sem reiniciar (SPI_SETCURSORS).
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import zipfile
from pathlib import Path

from . import config, curio, paths, winapi

# Papéis de cursor do Windows (valores de HKCU\Control Panel\Cursors)
ROLES = ["Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen",
         "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand"]

CURSORS_REG = r"Control Panel\Cursors"

# Pacotes conhecidos (baixados do GitHub na primeira execução ou sob demanda)
KNOWN_DOWNLOADS = [
    {"key": "macos", "title": "macOS", "repo": "ful1e5/apple_cursor", "asset": "macOS-Windows.zip"},
    {"key": "macos-white", "title": "macOS White", "repo": "ful1e5/apple_cursor", "asset": "macOS-White-Windows.zip"},
    {"key": "bibata-ice", "title": "Bibata Modern Ice", "repo": "ful1e5/Bibata_Cursor", "asset": "Bibata-Modern-Ice-Windows.zip"},
    {"key": "bibata-amber", "title": "Bibata Modern Amber", "repo": "ful1e5/Bibata_Cursor", "asset": "Bibata-Modern-Amber-Windows.zip"},
    {"key": "breezex-dark", "title": "BreezeX Dark", "repo": "ful1e5/BreezeX_Cursor", "asset": "BreezeX-Dark-Windows.zip"},
    {"key": "breezex-black", "title": "BreezeX Black", "repo": "ful1e5/BreezeX_Cursor", "asset": "BreezeX-Black-Windows.zip"},
    {"key": "breezex-light", "title": "BreezeX Light", "repo": "ful1e5/BreezeX_Cursor", "asset": "BreezeX-Light-Windows.zip"},
]

# ------------------------------------------------------------------ INF

_ROLE_RE = re.compile(
    r'HKCU\s*,\s*"Control Panel\\Cursors"\s*,\s*([A-Za-z]*)\s*,\s*(?:0x[0-9A-Fa-f]+|\d+)\s*,\s*"([^"]*)"')
_STR_RE = re.compile(r'^\s*([A-Za-z0-9_\-\.]+)\s*=\s*"([^"]*)"', re.M)


def parse_inf_text(text: str) -> dict:
    """Extrai (nome do esquema, papel → arquivo) de um install.inf.

    Lida com valores tipo "%10%\%CUR_DIR%\Pointer.cur" e nomes simples "arrow.cur".
    """
    strings: dict[str, str] = {}
    m = re.search(r"\[Strings\](.*?)(\n\[|\Z)", text, re.S | re.I)
    if m:
        for k, v in _STR_RE.findall(m.group(1)):
            strings[k.upper()] = v

    def expand(v: str) -> str:
        def rep(mm):
            key = mm.group(1).upper()
            if key == "10":  # %10% = pasta do Windows
                return ""
            return strings.get(key, mm.group(0))
        return re.sub(r"%([A-Za-z0-9_\-\.]+)%", rep, v)

    name = None
    for key in ("CUR_SCHEME_NAME", "CURSOR", "SCHEME"):
        if key in strings:
            name = strings[key]
            break

    roles: dict[str, str] = {}
    for role, value in _ROLE_RE.findall(text):
        value = expand(value).strip()
        if not value:
            if role == "" and not name:
                name = ""
            continue
        fname = Path(value.replace("\\", "/")).name
        if role == "":
            continue  # valor padrão = nome do esquema
        if role in ROLES and fname.lower() not in ("", "(default)"):
            roles[role] = fname
    if not name:
        name = strings.get("CUR_DIR", "").replace("Cursors\\", "").strip() or None
    return {"name": name, "roles": roles}


def parse_inf_file(inf_path: Path) -> dict:
    try:
        text = inf_path.read_text("utf-8", errors="replace")
        if "\x00" in text[:200]:
            text = text.encode("latin-1", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return {"name": None, "roles": {}}
    return parse_inf_text(text)


def _find_file(root: Path, fname: str) -> Path | None:
    """Procura um arquivo (case-insensitive) dentro do diretório do pacote."""
    target = fname.lower()
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name.lower() == target:
            return p
    return None


_FALLBACK_HINTS = [
    ("Arrow", ("arrow", "pointer", "left_ptr", "normal")),
    ("Wait", ("wait", "busy")),
    ("AppStarting", ("working", "appstart", "left_ptr_watch", "progress")),
    ("Hand", ("link", "hand", "select")),
    ("IBeam", ("ibeam", "text")),
    ("Crosshair", ("cross",)),
    ("No", ("no", "unavailable", "not-allowed", "crossed")),
    ("SizeAll", ("move", "all-scroll", "sizeall")),
    ("NWPen", ("pen", "nwpen")),
    ("Help", ("help",)),
    ("SizeNS", ("ns", "v_double")),
    ("SizeWE", ("we", "h_double")),
    ("SizeNWSE", ("nwse",)),
    ("SizeNESW", ("nesw",)),
    ("UpArrow", ("up", "alternate")),
]


def roles_from_folder(folder: Path) -> dict[str, Path]:
    """Adivinha papéis pelos nomes dos arquivos (para zips sem install.inf)."""
    files = [p for p in folder.rglob("*") if p.suffix.lower() in (".cur", ".ani", ".ico")]
    out: dict[str, Path] = {}
    used: set[Path] = set()
    for role, hints in _FALLBACK_HINTS:
        for p in files:
            if p in used:
                continue
            stem = p.stem.lower()
            if any(h in stem for h in hints):
                out[role] = p
                used.add(p)
                break
    return out


# ------------------------------------------------- instalação de pacotes

def install_from_zip(zip_path, dest_root: Path | None = None) -> list[str]:
    """Extrai um zip de cursores e instala os pacotes que ele contém.

    Retorna a lista de nomes de pacotes instalados."""
    zip_path = Path(zip_path)
    dest_root = dest_root or paths.packs_root()
    dest_root.mkdir(parents=True, exist_ok=True)
    tmp = paths.temp_dir() / f"pack_{zip_path.stem}"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)

    # procura todos os install.inf (um por esquema/variante)
    infs = sorted(tmp.rglob("*.inf"))
    installed: list[str] = []
    if infs:
        for i, inf in enumerate(infs):
            parsed = parse_inf_file(inf)
            folder = inf.parent
            base_name = parsed["name"] or (folder.name or zip_path.stem)
            name = base_name if i == 0 else f"{base_name} ({i + 1})"
            _copy_pack(folder, dest_root / _safe_name(name), name)
            installed.append(name)
    else:
        # sem INF: instala cada pasta com cursores usando heurística de nomes
        folders = [d for d in sorted(tmp.rglob("*")) if d.is_dir()] or [tmp]
        idx = 0
        for folder in folders:
            if not any(p.suffix.lower() in (".cur", ".ani") for p in folder.rglob("*")):
                continue
            name = folder.name or zip_path.stem
            if name.lower() in {n.lower() for n in installed}:
                idx += 1
                name = f"{name} {idx + 1}"
            _copy_pack(folder, dest_root / _safe_name(name), name)
            installed.append(name)
    shutil.rmtree(tmp, ignore_errors=True)
    return installed


def install_from_dir(src: Path, dest_root: Path | None = None) -> list[str]:
    src = Path(src)
    dest_root = dest_root or paths.packs_root()
    name = src.name
    inf = next(src.rglob("*.inf"), None)
    parsed = parse_inf_file(inf) if inf else {"name": None, "roles": {}}
    name = parsed["name"] or name
    _copy_pack(src, dest_root / _safe_name(name), name)
    return [name]


def _safe_name(name: str) -> str:
    keep = "".join(c if (c.isalnum() or c in " -_()") else "_" for c in name)
    return keep.strip() or "Pacote"


def _copy_pack(src: Path, dest: Path, name: str) -> None:
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)
    meta = {"name": name}
    try:
        (dest / "pack.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    except Exception:
        pass


# ------------------------------------------------------------------ scan

def scan_packs() -> list[dict]:
    """Lista pacotes instalados: {name, dir, roles: {papel: caminho}, arrow: PIL|None}."""
    root = paths.packs_root()
    packs: list[dict] = []
    seen: set[str] = set()
    if not root.exists():
        return packs
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        info = pack_info(folder)
        if info and info["name"].lower() not in seen:
            seen.add(info["name"].lower())
            packs.append(info)
    return packs


def pack_info(folder: Path) -> dict | None:
    folder = Path(folder)
    inf = next(folder.rglob("*.inf"), None)
    parsed = parse_inf_file(inf) if inf else {"name": None, "roles": {}}
    roles_files: dict[str, Path] = {}
    if parsed["roles"]:
        for role, fname in parsed["roles"].items():
            f = _find_file(folder, fname)
            if f:
                roles_files[role] = f
    if not roles_files:
        roles_files = roles_from_folder(folder)
    if not roles_files:
        return None
    meta = {}
    try:
        meta = json.loads((folder / "pack.json").read_text("utf-8"))
    except Exception:
        pass
    name = meta.get("name") or parsed["name"] or folder.name
    arrow_img = None
    try:
        if "Arrow" in roles_files:
            arrow_img, _ = curio.read_cursor_file(roles_files["Arrow"])
    except Exception:
        arrow_img = None
    return {"name": name, "dir": folder, "roles": roles_files, "arrow": arrow_img}


# ------------------------------------------------- backup / aplicar / restaurar

def _read_cursor_reg() -> dict:
    out: dict = {}
    if not winapi.IS_WINDOWS:
        return out
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CURSORS_REG) as k:
            try:
                out["(Default)"], _ = winreg.QueryValueEx(k, "")
            except OSError:
                out["(Default)"] = ""
            for role in ROLES:
                try:
                    out[role], _ = winreg.QueryValueEx(k, role)
                except OSError:
                    pass
    except Exception:
        pass
    return out


def backup_current() -> None:
    try:
        paths.backup_file().write_text(json.dumps(_read_cursor_reg(), ensure_ascii=False), "utf-8")
    except Exception:
        pass


def restore_backup() -> bool:
    """Volta os cursores para o estado anterior à última troca feita pelo app."""
    try:
        data = json.loads(paths.backup_file().read_text("utf-8"))
    except Exception:
        return False
    if not winapi.IS_WINDOWS:
        return False
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_REG, 0, winreg.KEY_SET_VALUE) as k:
        for role in ROLES:
            if role in data:
                winreg.SetValueEx(k, role, 0, winreg.REG_SZ, data[role])
            else:
                try:
                    winreg.DeleteValue(k, role)
                except OSError:
                    pass
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, data.get("(Default)", ""))
    winapi.refresh_cursors()
    config.set("cursor.active", data.get("(Default)", "") or "Restaurado")
    return True


def restore_windows_default() -> None:
    """Remove todos os cursores personalizados (volta ao padrão do tema do Windows)."""
    backup_current()
    active = paths.active_cursor_dir()
    if active.exists():
        shutil.rmtree(active, ignore_errors=True)
    if winapi.IS_WINDOWS:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_REG, 0, winreg.KEY_SET_VALUE) as k:
            for role in ROLES:
                try:
                    winreg.DeleteValue(k, role)
                except OSError:
                    pass
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Windows Padrão")
    winapi.refresh_cursors()
    config.set("cursor.active", "Windows Padrão")
    config.set("cursor.custom_image", "")


def _copy_to_active(src: Path, role: str) -> str:
    active = paths.active_cursor_dir()
    active.mkdir(parents=True, exist_ok=True)
    dest = active / f"{role}{src.suffix.lower()}"
    shutil.copy2(src, dest)
    return str(dest)


def apply_pack(pack: dict) -> bool:
    """Aplica um pacote escaneado (pack_info) como cursor do sistema."""
    backup_current()
    if not winapi.IS_WINDOWS:
        return False
    import winreg
    active = paths.active_cursor_dir()
    if active.exists():
        shutil.rmtree(active, ignore_errors=True)
    found = {role: _copy_to_active(src, role) for role, src in pack["roles"].items()}
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_REG, 0, winreg.KEY_SET_VALUE) as k:
        for role in ROLES:
            if role in found:
                winreg.SetValueEx(k, role, 0, winreg.REG_SZ, found[role])
            else:
                try:
                    winreg.DeleteValue(k, role)
                except OSError:
                    pass
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, pack["name"])
    winapi.refresh_cursors()
    config.set("cursor.active", pack["name"])
    return True


def apply_image_cursor(image_path, size: int = 32, hotspot_frac=(0.0, 0.0),
                       also_hand: bool = False) -> bool:
    """Transforma uma imagem qualquer no cursor do sistema (ponta = hotspot)."""
    if not winapi.IS_WINDOWS:
        return False
    img, _ = curio.read_cursor_file(image_path)
    w, h = img.size
    scale = min(size / max(1, w), size / max(1, h))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    hx = max(0, min(nw - 1, int(hotspot_frac[0] * w * scale)))
    hy = max(0, min(nh - 1, int(hotspot_frac[1] * h * scale)))

    active = paths.active_cursor_dir()
    if active.exists():
        shutil.rmtree(active, ignore_errors=True)
    active.mkdir(parents=True, exist_ok=True)
    arrow = active / "Arrow.cur"
    curio.write_cur(img, arrow, (hx, hy))

    backup_current()
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CURSORS_REG, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "Arrow", 0, winreg.REG_SZ, str(arrow))
        if also_hand and "Hand" in ROLES:
            hand = active / "Hand.cur"
            curio.write_cur(img, hand, (hx, hy))
            winreg.SetValueEx(k, "Hand", 0, winreg.REG_SZ, str(hand))
        for role in ROLES:
            if role in ("Arrow", "Hand") and (role != "Hand" or also_hand):
                continue
            try:
                winreg.DeleteValue(k, role)
            except OSError:
                pass
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Personalizado (imagem)")
    winapi.refresh_cursors()
    config.set("cursor.active", "Personalizado (imagem)")
    config.set("cursor.custom_image", str(image_path))
    return True


def current_scheme() -> str:
    if not winapi.IS_WINDOWS:
        return config.get("cursor.active", "") or ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CURSORS_REG) as k:
            v, _ = winreg.QueryValueEx(k, "")
            return v or ""
    except Exception:
        return ""
