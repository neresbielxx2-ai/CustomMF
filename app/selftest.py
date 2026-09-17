"""Autoteste do Custom MF: núcleo sempre; UI quando há display (roda no CI Windows)."""
from __future__ import annotations

import os
import struct
import sys
import tempfile
import traceback
from pathlib import Path

from PIL import Image


def _check(name, fn, results):
    try:
        fn()
        results.append((name, True, ""))
        print(f"  ✔ {name}")
    except Exception as e:  # noqa
        results.append((name, False, f"{e}\n{traceback.format_exc()}"))
        print(f"  ✖ {name}: {e}")


def test_config():
    from app.core import config, paths
    tmp = tempfile.mkdtemp()
    os.environ["APPDATA"] = tmp
    import importlib
    importlib.reload(paths)
    importlib.reload(config)
    config.load()
    config.set("fx.click_type", "fogos")
    assert config.get("fx.click_type") == "fogos"
    config.load()  # recarrega do disco
    assert config.get("fx.click_type") == "fogos"
    config.set("fx.click_type", "onda")
    config.reset_theme()
    assert config.get("theme.accent") == "#7C5CFF"


def test_inf_parser():
    from app.core.cursors import parse_inf_text
    inf_a = """
[Version]
signature="$CHICAGO$"

[Strings]
CUR_DIR = "Cursors\\macOS"
CUR_SCHEME_NAME = "macOS"

[Scheme.Reg]
HKCU,"Control Panel\\Cursors",Scheme Source,0x00020000,"0"
HKCU,"Control Panel\\Cursors",,0x00020000,"%CUR_SCHEME_NAME%"
HKCU,"Control Panel\\Cursors",Arrow,0x00020000,"%10%\\%CUR_DIR%\\Pointer.cur"
HKCU,"Control Panel\\Cursors",Wait,0x00020000,"%10%\\%CUR_DIR%\\Busy.ani"
HKCU,"Control Panel\\Cursors",Hand,0x00020000,"%10%\\%CUR_DIR%\\Link.cur"
"""
    r = parse_inf_text(inf_a)
    assert r["name"] == "macOS", r
    assert r["roles"]["Arrow"] == "Pointer.cur", r
    assert r["roles"]["Wait"] == "Busy.ani"
    assert r["roles"]["Hand"] == "Link.cur"

    inf_b = """
[Strings]
CUR_SCHEME_NAME = "Bibata Modern Ice"
[Scheme.Reg]
HKCU,"Control Panel\\Cursors",Arrow,0x00020000,"left_ptr.cur"
HKCU,"Control Panel\\Cursors",IBeam,0x00020000,"xterm.cur"
"""
    r2 = parse_inf_text(inf_b)
    assert r2["name"] == "Bibata Modern Ice"
    assert r2["roles"]["Arrow"] == "left_ptr.cur"
    assert r2["roles"]["IBeam"] == "xterm.cur"


def test_cur_roundtrip():
    from app.core import curio
    img = Image.new("RGBA", (32, 32), (200, 40, 90, 255))
    for x in range(8):
        for y in range(8):
            img.putpixel((x, y), (0, 255, 0, 255))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.cur"
        curio.write_cur(img, p, (1, 2))
        data = p.read_bytes()
        _, typ, count = struct.unpack("<HHH", data[:6])
        assert typ == 2 and count == 1
        hx, hy = struct.unpack("<HH", data[10:14])
        assert (hx, hy) == (1, 2)
        back, hotspot = curio.read_cur(p)
        assert back.size == (32, 32)
        assert hotspot == (1, 2)
        px = back.getpixel((2, 2))
        assert px[0] == 0 and px[1] == 255 and px[2] == 0, px  # verde
        px2 = back.getpixel((20, 20))
        assert px2[0] == 200 and px2[1] == 40 and px2[2] == 90, px2


def test_particles():
    from app.core.particles import Adapter, Engine

    class Rec(Adapter):
        def __init__(self):
            self.calls = []

        def ring(self, cx, cy, r, width, color):
            self.calls.append(("ring", r, color))

        def dot(self, cx, cy, r, color):
            self.calls.append(("dot", r, color))

        def glyph(self, cx, cy, ch, size, color):
            self.calls.append(("glyph", ch, color))

        def line(self, x1, y1, x2, y2, w, color):
            self.calls.append(("line", color))

    eng = Engine(Rec())
    cfg = {"click_enabled": True, "click_type": "onda", "click_color": "#FF0000",
           "click_rainbow": False, "click_size": 1.0, "click_duration": 1.0,
           "trail_enabled": True, "trail_type": "neon", "trail_color": "#00FF00",
           "trail_rainbow": False, "trail_size": 1.0, "trail_density": 3,
           "trail_duration": 1.0}
    eng.click(10, 10, cfg)
    assert eng.p, "clique não gerou partículas"
    eng.trail_spawn(20, 12, cfg, 10, 10)
    assert eng.p
    import time as _t
    eng.step(now=_t.monotonic(), bg="#010203")
    assert eng.a.calls, "step não desenhou"
    for kind in ("pulso", "faiscas", "estrelas", "coracoes", "flash", "fogos"):
        eng2 = Engine(Rec())
        c2 = dict(cfg, click_type=kind)
        eng2.click(0, 0, c2)
        assert eng2.p, f"tipo {kind} não gerou partículas"
    for kind in ("bolhas", "estrelas", "coracoes", "fogo", "po"):
        eng3 = Engine(Rec())
        c3 = dict(cfg, trail_type=kind)
        eng3.trail_spawn(5, 5, c3)
        assert eng3.p, f"trilha {kind} não gerou partículas"


def test_iconpacks():
    from app.core import iconpacks
    packs = iconpacks.list_packs()
    for name in ("Neon Padrão", "Minimal"):
        assert name in packs
    for key in iconpacks.KEYS:
        assert key in packs["Neon Padrão"]["glyphs"]
    active = iconpacks.get_active()
    assert active["name"] in packs


def test_known_downloads():
    from app.core.cursors import KNOWN_DOWNLOADS
    assert any(k["key"] == "macos" for k in KNOWN_DOWNLOADS)
    for k in KNOWN_DOWNLOADS:
        assert k["repo"].count("/") == 1
        assert "Windows" in k["asset"] or "windows" in k["asset"]


def test_ui():
    """Constrói a aplicação inteira (requer display)."""
    import customtkinter as ctk  # noqa: F401
    from app.main import App
    app = App(start="main")
    app.update()

    from app.ui.main_window import NAV
    mw = app.main_window
    assert mw is not None, "janela principal não construída"
    for key, _label, _icon in NAV:
        mw.show(key)
        app.update()
    mw.show("home")
    app.update()

    from app.core.effects import FXOverlay
    assert isinstance(app.overlay, FXOverlay)

    app.destroy()


def run_selftest(ui: bool = True) -> int:
    print("Custom MF — autoteste")
    results = []
    _check("config", test_config, results)
    _check("inf parser", test_inf_parser, results)
    _check("cur roundtrip", test_cur_roundtrip, results)
    _check("particles", test_particles, results)
    _check("icon packs", test_iconpacks, results)
    _check("downloads conhecidos", test_known_downloads, results)
    if ui:
        try:
            import tkinter  # noqa: F401
            has_display = True
        except Exception:
            has_display = False
        if has_display:
            _check("ui completa", test_ui, results)
        else:
            print("  – ui pulada (sem display)")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} testes passaram")
    if failed:
        for name, _ok, tb in failed:
            print(f"--- FALHOU: {name}\n{tb}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_selftest(ui="--no-ui" not in sys.argv))
