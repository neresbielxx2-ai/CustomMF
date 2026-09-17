"""Ponto de entrada da aplicação Custom MF."""
from __future__ import annotations

import ctypes
import sys
import traceback

import customtkinter as ctk

from . import __version__
from .core import config, paths, theme, winapi

SPLASH_W, SPLASH_H = 560, 430
MAIN_W, MAIN_H = 1180, 740
MIN_W, MIN_H = 980, 620


class App(ctk.CTk):
    def __init__(self, start: str = "splash"):
        super().__init__()
        config.load()
        self.title("Custom MF — Personalize seu Windows")
        self._center(SPLASH_W, SPLASH_H)
        self.resizable(True, True)
        self.minsize(SPLASH_W, SPLASH_H)
        self.configure(fg_color=theme.tokens()["bg"])
        try:
            self.iconbitmap(str(paths.asset("icon.ico")))
        except Exception:
            pass

        if not winapi.acquire_single_instance():
            ctypes.windll.user32.MessageBoxW(
                0, "O Custom MF já está em execução.\nDê uma olhada na bandeja/barra de tarefas 😉",
                "Custom MF", 0x40)
            self.after(50, self.destroy)
            return

        self.overlay = None
        self.main_window = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if start == "splash":
            self.minsize(SPLASH_W, SPLASH_H)
            from .ui.splash import Splash
            self._splash = Splash(self, self._enter_main)
        else:
            self._enter_main_instant()

    # ------------------------------------------------------------ janela

    def _center(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 3)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _enter_main(self):
        t = theme.tokens()
        self.minsize(MIN_W, MIN_H)
        self.resizable(True, True)
        # animação de crescimento da janela
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w0, h0 = SPLASH_W, SPLASH_H
        w1, h1 = min(MAIN_W, sw - 40), min(MAIN_H, sh - 60)
        steps = 16
        self._grow(0, steps, w0, h0, w1, h1, sw, sh)

    def _grow(self, i, steps, w0, h0, w1, h1, sw, sh):
        p = i / steps
        ease = 1 - (1 - p) ** 3
        w = int(w0 + (w1 - w0) * ease)
        h = int(h0 + (h1 - h0) * ease)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 3)
        try:
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            return
        if i < steps:
            self.after(11, lambda: self._grow(i + 1, steps, w0, h0, w1, h1, sw, sh))
        else:
            from .core.effects import FXOverlay
            from .ui.main_window import MainWindow
            self.overlay = FXOverlay(self)
            self.main_window = MainWindow(self, self.overlay)
            self.overlay.update_state()

    # ------------------------------------------------------------ misc

    def rebuild_ui(self):
        if self.main_window:
            self.main_window.rebuild()
        if self.overlay:
            self.overlay.update_state()

    def _on_close(self):
        try:
            if self.overlay:
                self.overlay.stop()
        except Exception:
            pass
        self.destroy()


def _selftest(argv) -> int:
    from .selftest import run_selftest
    return run_selftest(ui="--no-ui" not in argv)


def run():
    argv = sys.argv[1:]
    try:
        if "--selftest" in argv:
            sys.exit(_selftest(argv))
        ctk.set_appearance_mode(theme.ctk_appearance())
        app = App(start="splash")
        app.mainloop()
    except Exception:
        try:
            log = paths.crash_log()
            log.write_text(traceback.format_exc(), "utf-8")
            if winapi.IS_WINDOWS:
                ctypes.windll.user32.MessageBoxW(
                    0, f"Ocorreu um erro inesperado.\nDetalhes salvos em:\n{log}",
                    "Custom MF", 0x10)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    run()
