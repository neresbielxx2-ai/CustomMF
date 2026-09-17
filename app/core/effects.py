"""Overlay global em tela cheia: desenha efeitos de clique e trilhas do mouse.

Janela transparente, sempre no topo e "atravessável" (cliques passam direto).
Funciona enquanto o app estiver aberto.
"""
from __future__ import annotations

import time

import tkinter as tk

from . import config, particles, winapi

TRANSPARENT = "#010203"  # cor que fica invisível (transparentcolor)


class FXOverlay:
    def __init__(self, root: tk.Misc):
        self.root = root
        self.win: tk.Toplevel | None = None
        self.engine: particles.Engine | None = None
        self._running = False
        self._prev_left = False
        self._prev_right = False
        self._last = (0.0, 0.0)
        self._accum = 0.0
        self._last_spawn = 0.0

    # ------------------------------------------------------------ estado

    @property
    def running(self) -> bool:
        return self._running

    def update_state(self) -> None:
        """Liga/desliga conforme as configurações."""
        should = (config.get("fx.click_enabled") or config.get("fx.trail_enabled")) and winapi.IS_WINDOWS
        if should and not self._running:
            self.start()
        elif not should and self._running:
            self.stop()

    # ------------------------------------------------------------- ciclo

    def start(self) -> None:
        if self._running or not winapi.IS_WINDOWS:
            return
        try:
            win = tk.Toplevel(self.root, bg=TRANSPARENT)
            win.overrideredirect(True)
            vx, vy, vw, vh = winapi.virtual_screen()
            win.geometry(f"{vw}x{vh}+{vx}+{vy}")
            try:
                win.attributes("-transparentcolor", TRANSPARENT)
            except Exception:
                pass
            win.attributes("-topmost", True)
            canvas = tk.Canvas(win, bg=TRANSPARENT, highlightthickness=0, bd=0)
            canvas.pack(fill="both", expand=True)
            try:
                winapi.make_clickthrough(winapi.toplevel_hwnd(win))
            except Exception:
                pass
            self.win = win
            self.canvas = canvas
            self.engine = particles.Engine(particles.CanvasAdapter(canvas))
            self._vx, self._vy = vx, vy
            self._prev_left = winapi.key_down(winapi.VK_LBUTTON)
            self._prev_right = winapi.key_down(winapi.VK_RBUTTON)
            self._last = (0.0, 0.0)
            self._accum = 0.0
            self._running = True
            win.protocol("WM_DELETE_WINDOW", self.stop)
            self.root.after(16, self._loop)
        except Exception:
            self._running = False

    def stop(self) -> None:
        self._running = False
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
            self.win = None

    def test_click(self) -> None:
        """Dispara um efeito na posição atual do cursor (botão Testar)."""
        pos = winapi.get_cursor_pos()
        if pos and self.engine and self._running:
            self.engine.click(pos[0] - self._vx, pos[1] - self._vy, dict(config.get("fx", {})))

    # -------------------------------------------------------------- loop

    def _loop(self) -> None:
        if not self._running or self.win is None:
            return
        try:
            if not self.win.winfo_exists():
                self._running = False
                return
        except Exception:
            self._running = False
            return

        cfg = dict(config.get("fx", {}))
        eng = self.engine
        pos = winapi.get_cursor_pos()
        now_s = time.monotonic()

        if pos is not None:
            x, y = pos[0] - self._vx, pos[1] - self._vy
            if cfg.get("trail_enabled"):
                lx, ly = self._last
                dist = ((x - lx) ** 2 + (y - ly) ** 2) ** 0.5
                need = particles.Engine.trail_interval_px(cfg.get("trail_density", 3))
                if self._last == (0.0, 0.0):
                    self._last = (x, y)
                elif dist >= need and now_s - self._last_spawn > 0.012:
                    eng.trail_spawn(x, y, cfg, lx, ly)
                    self._last = (x, y)
                    self._last_spawn = now_s
            else:
                self._last = (x, y)

            # efeitos de clique (detecta borda de pressão dos botões)
            left = winapi.key_down(winapi.VK_LBUTTON)
            right = winapi.key_down(winapi.VK_RBUTTON)
            if left and not self._prev_left:
                eng.click(x, y, cfg, 1)
            if right and not self._prev_right:
                eng.click(x, y, cfg, 2)
            self._prev_left, self._prev_right = left, right

        if eng is not None:
            eng.step(now_s, TRANSPARENT)
        self.root.after(12, self._loop)
