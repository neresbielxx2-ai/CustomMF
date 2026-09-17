"""Página Efeitos de Clique: escolha do efeito, cor, tamanho e teste ao vivo."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ...core import config, particles
from .. import widgets as W


class ClickPage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()
        self.engine = None

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 10))

        W.section_header(wrap, "✨", "Efeitos de Clique",
                         "Animações que aparecem em qualquer lugar do Windows quando você clica. "
                         "O app precisa continuar aberto.").pack(fill="x")

        toggle = W.ToggleRow(wrap, "Ativar efeitos de clique",
                             "um brilho em todo clique — esquerdo e direito",
                             checked=config.get("fx.click_enabled"), icon="⚡",
                             command=self._toggle)
        toggle.pack(fill="x", pady=(0, 14))

        # tipos
        types_card = W.Card(wrap)
        types_card.pack(fill="x", pady=(0, 14))
        box = ctk.CTkFrame(types_card, fg_color="transparent")
        box.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(box, text="Tipo de efeito", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w", pady=(0, 8))
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x")
        self.type_btns = {}
        cur = config.get("fx.click_type", "onda")
        for i, key in enumerate(particles.CLICK_TYPES):
            b = self._type_btn(grid, key, cur == key)
            b.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="ew")
            grid.grid_columnconfigure(i % 4, weight=1)

        # cor + sliders
        opts = W.Card(wrap)
        opts.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(opts, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        rainbow = config.get("fx.click_color", "") == "rainbow"
        self.color_row = W.ColorRow(inner, "Cor do efeito",
                                    value=config.get("fx.click_color", "#7C5CFF"),
                                    rainbow=rainbow, on_change=self._set_color)
        self.color_row.pack(fill="x", pady=(0, 10))
        self.size_row = W.SliderRow(inner, "Tamanho", 0.5, 2.5, config.get("fx.click_size", 1.0),
                                    command=self._set_size)
        self.size_row.pack(fill="x", pady=(0, 6))
        self.dur_row = W.SliderRow(inner, "Duração", 0.5, 2.0, config.get("fx.click_duration", 1.0),
                                   command=self._set_duration)
        self.dur_row.pack(fill="x")

        # preview
        prev_card = W.Card(wrap)
        prev_card.pack(fill="x")
        pbox = ctk.CTkFrame(prev_card, fg_color="transparent")
        pbox.pack(fill="both", expand=True, padx=16, pady=14)
        row = ctk.CTkFrame(pbox, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Teste ao vivo", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(side="left")
        W.ghost_button(row, "🖥️  Testar na tela real", self._test_screen).pack(side="right")
        self.preview = tk.Canvas(pbox, height=190, bg=t["bg_deep"], highlightthickness=1,
                                 highlightbackground=t["border"], cursor="crosshair")
        self.preview.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(pbox, text="👆 clique dentro da área para ver o efeito",
                     font=W.fnt(10), text_color=t["sub"]).pack(anchor="center", pady=(4, 0))

        self.engine = particles.Engine(particles.CanvasAdapter(self.preview))
        self.preview.bind("<Button-1>", self._preview_click)
        self._loop()

    def _type_btn(self, parent, key, selected):
        t = self.t
        label = particles.CLICK_LABELS[key]

        def cmd():
            config.set("fx.click_type", key)
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
        config.set("fx.click_enabled", on)
        if self.app.overlay:
            self.app.overlay.update_state()

    def _set_color(self, v):
        config.set("fx.click_color", v)
        config.set("fx.click_rainbow", v == "rainbow")

    def _set_size(self, v):
        config.set("fx.click_size", v)

    def _set_duration(self, v):
        config.set("fx.click_duration", v)

    def _preview_click(self, ev):
        if self.engine:
            cfg = dict(config.get("fx", {}))
            cfg["click_enabled"] = True
            self.engine.click(ev.x, ev.y, cfg)

    def _test_screen(self):
        if self.app.overlay and self.app.overlay.running:
            self.app.overlay.test_click()
        else:
            if self.engine:
                cfg = dict(config.get("fx", {}))
                cfg["click_enabled"] = True
                self.engine.click(self.preview.winfo_width() / 2, 95, cfg)

    def _loop(self):
        try:
            if not self.preview.winfo_exists():
                return
        except Exception:
            return
        if self.engine:
            self.engine.step(bg=self._canvas_bg())
        self.preview.after(33, self._loop)

    def _canvas_bg(self):
        # cor "invisível" dentro da área de teste: usamos o fundo profundo como fade
        return self.t["bg_deep"]
