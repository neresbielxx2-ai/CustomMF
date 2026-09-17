"""Helpers do Windows via ctypes (sem dependências externas).

Tudo é protegido: em sistemas não-Windows as funções viram no-op para que a UI
possa ser construída em testes (CI/Linux) sem quebrar.
"""
from __future__ import annotations

import base64
import ctypes
import sys
import time

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import wintypes

    _u32 = ctypes.WinDLL("user32", use_last_error=True)
    _g32 = ctypes.WinDLL("gdi32", use_last_error=True)
    _sh32 = ctypes.WinDLL("shell32", use_last_error=True)
    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_NOACTIVATE = 0x08000000
    SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
    SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
    VK_LBUTTON, VK_RBUTTON = 0x01, 0x02
    SPI_SETCURSORS = 0x0057
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02


def _noop(*a, **k):
    return None


def get_cursor_pos() -> tuple[int, int] | None:
    """Posição física do cursor na tela."""
    if not IS_WINDOWS:
        return None
    pt = POINT()
    if _u32.GetCursorPos(ctypes.byref(pt)):
        return pt.x, pt.y
    return None


def key_down(vk: int) -> bool:
    if not IS_WINDOWS:
        return False
    return bool(_u32.GetAsyncKeyState(vk) & 0x8000)


def virtual_screen() -> tuple[int, int, int, int]:
    """Origin+size da área de trabalho virtual (todos os monitores)."""
    if not IS_WINDOWS:
        return 0, 0, 1280, 720
    x = _u32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = _u32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = _u32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = _u32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return x, y, max(1, w), max(1, h)


def make_clickthrough(hwnd: int) -> None:
    """Torna a janela transparente a cliques (efeitos não bloqueiam o mouse)."""
    if not IS_WINDOWS or not hwnd:
        return
    user32 = _u32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def toplevel_hwnd(widget) -> int:
    """HWND real da janela top-level de um widget do tkinter."""
    try:
        hwnd = int(widget.winfo_id(), 16) if isinstance(widget.winfo_id(), str) else int(widget.winfo_id())
    except Exception:
        return 0
    if IS_WINDOWS:
        parent = _u32.GetParent(hwnd)
        if parent:
            hwnd = parent
    return hwnd


def refresh_cursors() -> None:
    """Aplica os cursores do registro sem precisar reiniciar/logoff."""
    if not IS_WINDOWS:
        return
    _u32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)


def is_admin() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        return bool(_sh32.IsUserAnAdmin())
    except Exception:
        return False


def run_elevated_powershell(script: str) -> bool:
    """Executa um script PowerShell como administrador (prompt UAC)."""
    if not IS_WINDOWS:
        return False
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    args = f'-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand {encoded}'
    code = _sh32.ShellExecuteW(None, "runas", "powershell.exe", args, None, 0)
    return int(code) > 32


def add_font_resource(path: str) -> None:
    if not IS_WINDOWS:
        return
    try:
        _g32.AddFontResourceW(str(path))
    except Exception:
        pass


def broadcast_font_change() -> None:
    if not IS_WINDOWS:
        return
    try:
        res = ctypes.c_ulong(0)
        _u32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 2, 1000, ctypes.byref(res))
    except Exception:
        pass


_already_has_mutex = False


def acquire_single_instance() -> bool:
    """True se esta é a única instância rodando."""
    global _already_has_mutex
    if not IS_WINDOWS:
        return True
    if _already_has_mutex:
        return True
    _k32.CreateMutexW(None, False, "Global\\CustomMF_SingleInstance")
    return _k32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def flash_window(widget) -> None:
    if not IS_WINDOWS:
        return
    hwnd = toplevel_hwnd(widget)
    if hwnd:
        try:
            class FLASHWINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("hwnd", ctypes.c_void_p),
                            ("dwFlags", ctypes.c_uint), ("uCount", ctypes.c_uint),
                            ("dwTimeout", ctypes.c_uint)]
            info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 0x0C, 2, 0)  # FLASHW_ALL|FLASHW_TIMERNOFG
            _u32.FlashWindowEx(ctypes.byref(info))
        except Exception:
            pass


def sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000.0)
