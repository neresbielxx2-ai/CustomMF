"""Página Trilhas: rastro animado que segue o cursor do mouse."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ...core import config, particles
from .. import widgets as W


class TrailsPage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()
        self.engine = None
        self._last = None

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 10))

        W.section_header(wrap, "🌈", "Trilhas Animadas",
                         "Um rastro de partículas que segue o seu cursor por toda a tela. "
                         "O app precisa continuar aberto.").pack(fill="x")

        toggle = W.ToggleRow(wrap, "Ativar trilha do mouse",
                             "partículas surgem conforme você move o cursor",
                             checked=config.get("fx.trail_enabled"), icon="💫",
                             command=self._toggle)
        toggle.pack(fill="x", pady=(0, 14))

        types_card = W.Card(wrap)
        types_card.pack(fill="x", pady=(0, 14))
        box = ctk.CTkFrame(types_card, fg_color="transparent")
        box.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(box, text="Estilo da trilha", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w", pady=(0, 8))
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x")
        self.type_btns = {}
        cur = config.get("fx.trail_type", "neon")
        for i, key in enumerate(particles.TRAIL_TYPES):
            b = self._type_btn(grid, key, cur == key)
            b.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="ew")
            grid.grid_columnconfigure(i % 4, weight=1)

        opts = W.Card(wrap)
        opts.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(opts, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        self.color_row = W.ColorRow(inner, "Cor da trilha",
                                    value=config.get("fx.trail_color", "#3DDC97"),
                                    rainbow=config.get("fx.trail_color") == "rainbow",
                                    on_change=self._set_color)
        self.color_row.pack(fill="x", pady=(0, 10))
        self.size_row = W.SliderRow(inner, "Tamanho das partículas", 0.5, 2.5,
                                    config.get("fx.trail_size", 1.0), command=self._set_size)
        self.size_row.pack(fill="x", pady=(0, 6))
        self.density_row = W.SliderRow(inner, "Densidade", 1, 5, config.get("fx.trail_density", 3),
                                       fmt=lambda v: f"{int(v)}/5", steps=4, command=self._set_density)
        self.density_row.pack(fill="x", pady=(0, 6))
        self.dur_row = W.SliderRow(inner, "Duração do rastro", 0.5, 2.0,
                                   config.get("fx.trail_duration", 1.0), command=self._set_duration)
        self.dur_row.pack(fill="x")

        prev_card = W.Card(wrap)
        prev_card.pack(fill="x")
        pbox = ctk.CTkFrame(prev_card, fg_color="transparent")
        pbox.pack(fill="both", expand=True, padx=16, pady=14)
        ctk.CTkLabel(pbox, text="Teste ao vivo", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        self.preview = tk.Canvas(pbox, height=200, bg=t["bg_deep"], highlightthickness=1,
                                 highlightbackground=t["border"])
        self.preview.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(pbox, text="👆 passe o mouse pela área para ver a trilha",
                     font=W.fnt(10), text_color=t["sub"]).pack(anchor="center", pady=(4, 0))

        self.engine = particles.Engine(particles.CanvasAdapter(self.preview))
        self.preview.bind("<Motion>", self._preview_motion)
        self._loop()

    def _type_btn(self, parent, key, selected):
        t = self.t
        label = particles.TRAIL_LABELS[key]

        def cmd():
            config.set("fx.trail_type", key)
            for k, b in self.type_btns.items():
                b.configure(fg_color=t["accent"] if k == key else t["hover_soft"],
                            text_color=t["on_accent"] if k == key else t["text"])

        b = ctk.CTkButton(parent, text=label, height=36, corner_radius=10, font=W.fnt(12, "bold"),
                          command=cmd,
                          fg_color=t["accent"] if selected else t["hover_soft"],
                          hover_color=t["border"],
                          text_color=t["on_accent"] if selected else t["text"])
        self.type_btns[key] = b
        return b

    def _toggle(self, on):
        config.set("fx.trail_enabled", on)
        if self.app.overlay:
            self.app.overlay.update_state()

    def _set_color(self, v):
        config.set("fx.trail_color", v)
        config.set("fx.trail_rainbow", v == "rainbow")

    def _set_size(self, v):
        config.set("fx.trail_size", v)

    def _set_density(self, v):
        config.set("fx.trail_density", int(v))

    def _set_duration(self, v):
        config.set("fx.trail_duration", v)

    def _preview_motion(self, ev):
        if not self.engine:
            return
        cfg = dict(config.get("fx", {}))
        cfg["trail_enabled"] = True
        if self._last is None:
            self._last = (ev.x, ev.y)
            return
        dist = ((ev.x - self._last[0]) ** 2 + (ev.y - self._last[1]) ** 2) ** 0.5
        need = particles.Engine.trail_interval_px(cfg.get("trail_density", 3)) * 0.35
        if dist >= need:
            self.engine.trail_spawn(ev.x, ev.y, cfg, self._last[0], self._last[1])
            self._last = (ev.x, ev.y)

    def _loop(self):
        try:
            if not self.preview.winfo_exists():
                return
        except Exception:
            return
        if self.engine:
            self.engine.step(bg=self.t["bg_deep"])
        self.preview.after(33, self._loop)
