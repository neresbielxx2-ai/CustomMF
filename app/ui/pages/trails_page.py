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
        self.type_btns: dict[str, ctk.CTkButton] = {}

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 14))

        W.section_header(wrap, "🌈", "Trilhas Animadas",
                         "Um rastro de partículas que segue o seu cursor por toda a tela — "
                         "sem atrapalhar cliques nem scroll. Deixe o app aberto.").pack(fill="x")

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
        cur = config.get("fx.trail_type", "neon")
        for i, key in enumerate(particles.TRAIL_TYPES):
            b = W.type_button(grid, particles.TRAIL_LABELS[key], cur == key,
                              lambda k=key: self._set_type(k))
            b.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="ew")
            grid.grid_columnconfigure(i % 4, weight=1)
            self.type_btns[key] = b

        opts = W.Card(wrap)
        opts.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(opts, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        W.ColorRow(inner, "Cor da trilha",
                   value=config.get("fx.trail_color", "#3DDC97"),
                   rainbow=config.get("fx.trail_color") == "rainbow",
                   on_change=self._set_color).pack(fill="x", pady=(0, 12))
        W.SliderRow(inner, "Tamanho das partículas", 0.5, 2.5,
                    config.get("fx.trail_size", 1.0), command=self._set_size
                    ).pack(fill="x", pady=(0, 8))
        W.SliderRow(inner, "Densidade", 1, 5, config.get("fx.trail_density", 3),
                    fmt=lambda v: f"{int(v)}/5", steps=4, command=self._set_density
                    ).pack(fill="x", pady=(0, 8))
        W.SliderRow(inner, "Duração do rastro", 0.5, 2.0,
                    config.get("fx.trail_duration", 1.0), command=self._set_duration).pack(fill="x")

        # preview
        prev_card = W.Card(wrap)
        prev_card.pack(fill="x")
        pbox = ctk.CTkFrame(prev_card, fg_color="transparent")
        pbox.pack(fill="both", expand=True, padx=16, pady=14)
        row = ctk.CTkFrame(pbox, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Teste ao vivo", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(side="left")
        W.chip(row, "passe o mouse pela área 👇", t["success"]).pack(side="left", padx=10)
        well = ctk.CTkFrame(pbox, corner_radius=14, fg_color=t["bg_deep"],
                            border_width=1, border_color=t["border"])
        well.pack(fill="x", pady=(12, 0))
        self.preview = tk.Canvas(well, height=200, bg=t["bg_deep"], highlightthickness=0)
        self.preview.pack(fill="both", expand=True, padx=2, pady=2)

        self.engine = particles.Engine(particles.CanvasAdapter(self.preview))
        self.preview.bind("<Motion>", self._preview_motion)
        self._loop()

    def _set_type(self, key):
        t = self.t
        config.set("fx.trail_type", key)
        for k, b in self.type_btns.items():
            sel = k == key
            b.configure(fg_color=t["accent"] if sel else t["hover_soft"],
                        text_color=t["on_accent"] if sel else t["text"])

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
