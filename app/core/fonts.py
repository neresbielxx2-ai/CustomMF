"""Troca da fonte padrão do Windows 10/11 (Segoe UI → a fonte escolhida).

Método clássico: HKLM\...\FontSubstitutes["Segoe UI"] = nome da fonte + entradas
de "Segoe UI (TrueType)" vazias. Requer admin (o app tenta direto e, sem
permissão, eleva via UAC). A troca completa aparece após sair da sessão.
Também instala fontes .ttf/.otf por usuário (sem admin).
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from . import paths, winapi

FONTS_REG = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
SUBSTITUTES_REG = r"Software\Microsoft\Windows NT\CurrentVersion\FontSubstitutes"

SEGOE_DEFAULTS = {
    "Segoe UI (TrueType)": "segoeui.ttf",
    "Segoe UI Bold (TrueType)": "segoeuib.ttf",
    "Segoe UI Bold Italic (TrueType)": "segoeuiz.ttf",
    "Segoe UI Italic (TrueType)": "segoeuii.ttf",
    "Segoe UI Semibold (TrueType)": "segoeuisb.ttf",
    "Segoe UI Semilight (TrueType)": "segoeuisl.ttf",
    "Segoe UI Light (TrueType)": "segoeuil.ttf",
    "Segoe UI Black (TrueType)": "segoeuib.ttf",
}


def installed_families() -> list[str]:
    try:
        import tkinter.font as tkfont
        fams = set(tkfont.families())
    except Exception:
        fams = set()
    for name in ("Segoe UI", "Arial", "Calibri"):
        fams.add(name)
    return sorted(fams)


def _internal_name(font_path: Path) -> str | None:
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(str(font_path), 14)
        family, _style = f.getname()
        return family
    except Exception:
        return None


def install_user_font(font_path) -> str:
    """Instala a fonte para o usuário atual (sem admin) e a disponibiliza já."""
    src = Path(font_path)
    if src.suffix.lower() not in (".ttf", ".otf", ".ttc"):
        raise ValueError("Escolha um arquivo .ttf, .otf ou .ttc")
    dest_dir = Path(winapi_local_fonts_dir())
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    i = 1
    while dest.exists():
        dest = dest_dir / f"{src.stem}_{i}{src.suffix}"
        i += 1
    shutil.copy2(src, dest)
    family = _internal_name(dest) or src.stem

    if winapi.IS_WINDOWS:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, FONTS_REG, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, f"{family} (TrueType)", 0, winreg.REG_SZ, str(dest))
    winapi.add_font_resource(str(dest))
    winapi.broadcast_font_change()

    backup = paths.fonts_dir() / dest.name
    try:
        shutil.copy2(dest, backup)
    except Exception:
        pass
    return family


def winapi_local_fonts_dir() -> str:
    import os
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData/Local")
    return str(Path(base) / "Microsoft" / "Windows" / "Fonts")


def current_substitute() -> str | None:
    if not winapi.IS_WINDOWS:
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SUBSTITUTES_REG) as k:
            v, _ = winreg.QueryValueEx(k, "Segoe UI")
            return v or None
    except Exception:
        return None


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _try_direct_write(mapping: dict, remove: list[str]) -> bool:
    """Tenta gravar em HKLM diretamente (funciona se o app já é admin)."""
    if not winapi.IS_WINDOWS:
        return False
    try:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, SUBSTITUTES_REG, 0,
                                winreg.KEY_SET_VALUE) as k:
            for name, value in mapping.items():
                winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
            for name in remove:
                try:
                    winreg.DeleteValue(k, name)
                except OSError:
                    pass
        return True
    except PermissionError:
        return False
    except Exception:
        return False


def _script_set(mapping: dict, remove: list[str]) -> str:
    lines = ["$ErrorActionPreference='Stop'",
             "$base='HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'"]
    for name, value in mapping.items():
        lines.append(f"New-ItemProperty -Path ($base+'\\FontSubstitutes') -Name {_ps_quote(name)} "
                     f"-Value {_ps_quote(value)} -PropertyType String -Force | Out-Null")
    for name in remove:
        lines.append(f"Remove-ItemProperty -Path ($base+'\\FontSubstitutes') -Name {_ps_quote(name)} "
                     f"-ErrorAction SilentlyContinue | Out-Null")
    for key, value in SEGOE_DEFAULTS.items():
        target = "''" if value == "" else _ps_quote(value)
        lines.append(f"New-ItemProperty -Path ($base+'\\Fonts') -Name {_ps_quote(key)} "
                     f"-Value {target} -PropertyType String -Force | Out-Null")
    lines.append("Write-Output 'OK'")
    return "\n".join(lines)


def apply_system_font(family: str) -> tuple[bool, str]:
    """Define `family` como fonte do sistema. Retorna (sucesso, mensagem)."""
    if not family or not family.strip():
        return False, "Escolha uma fonte."
    family = family.strip()
    if winapi.IS_WINDOWS and _try_direct_write({"Segoe UI": family}, []):
        return True, "Fonte aplicada! Saia da sessão (ou reinicie) para ver em todo o Windows."
    script = _script_set({"Segoe UI": family}, [])
    if not winapi.run_elevated_powershell(script):
        return False, "Você cancelou a permissão de administrador."
    for _ in range(20):
        time.sleep(0.4)
        cur = current_substitute()
        if cur and cur.lower() == family.lower():
            return True, "Fonte aplicada! Saia da sessão (ou reinicie) para ver em todo o Windows."
    return False, "Não foi possível confirmar a aplicação (a troca pode exigir reiniciar)."


def reset_system_font() -> tuple[bool, str]:
    """Volta para a Segoe UI original."""
    if winapi.IS_WINDOWS and _try_direct_write({}, ["Segoe UI"]):
        _restore_segoe_direct()
        return True, "Fonte padrão restaurada! Saia da sessão para concluir."
    script = _script_set({}, ["Segoe UI"])
    if not winapi.run_elevated_powershell(script):
        return False, "Você cancelou a permissão de administrador."
    for _ in range(20):
        time.sleep(0.4)
        if current_substitute() is None:
            return True, "Fonte padrão restaurada! Saia da sessão para concluir."
    return True, "Restauração enviada. Reinicie o PC para concluir."


def _restore_segoe_direct() -> None:
    try:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, FONTS_REG, 0, winreg.KEY_SET_VALUE) as k:
            for key, value in SEGOE_DEFAULTS.items():
                winreg.SetValueEx(k, key, 0, winreg.REG_SZ, value)
    except Exception:
        pass
