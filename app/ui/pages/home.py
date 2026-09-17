"""Página Início: boas-vindas, status e atalhos."""
from __future__ import annotations

import datetime
import tkinter as tk

import customtkinter as ctk

from ...core import config, cursors, theme
from .. import widgets as W

QUICK = [
    ("mouse", "🖱️", "Cursor", "Pacotes macOS, Bibata e o cursor feito da sua imagem."),
    ("click", "✨", "Efeitos de Clique", "Ondas, faíscas e fogos de artifício em cada clique."),
    ("trail", "🌈", "Trilhas Animadas", "Deixe um rastro neon, fogo ou arco-íris no mouse."),
    ("font", "🔤", "Fonte do Windows", "Troque a fonte do sistema e instale as suas .ttf."),
]


class HomePage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw

    def build(self, parent):
        t = W.T()
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(24, 10))

        h = datetime.datetime.now().hour
        sauda = "Bom dia" if 5 <= h < 12 else "Boa tarde" if 12 <= h < 18 else "Boa noite"
        ctk.CTkLabel(wrap, text=f"{sauda}! 👋", font=W.fnt(26, "bold"),
                     text_color=t["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(wrap, text="Deixe o seu Windows com a sua cara — cursor, efeitos, trilhas, fonte e ícones.",
                     font=W.fnt(13), text_color=t["sub"], anchor="w").pack(fill="x", pady=(2, 18))

        # status
        status = ctk.CTkFrame(wrap, fg_color=t["surface"], corner_radius=14)
        status.pack(fill="x", pady=(0, 18))
        box = ctk.CTkFrame(status, fg_color="transparent")
        box.pack(fill="x", padx=16, pady=12)
        scheme = cursors.current_scheme() or "padrão do Windows"
        fx_on = config.get("fx.click_enabled")
        tr_on = config.get("fx.trail_enabled")
        fonte = config.get("font.applied") or "Segoe UI (padrão)"
        for txt, color in [
            (f"🖱️ Cursor: {scheme}", t["accent"] if scheme not in ("", "Windows Padrão") else t["sub"]),
            (f"✨ Efeitos: {'ON' if fx_on else 'OFF'}", t["success"] if fx_on else t["sub"]),
            (f"🌈 Trilhas: {'ON' if tr_on else 'OFF'}", t["success"] if tr_on else t["sub"]),
            (f"🔤 Fonte: {fonte}", t["accent"] if config.get("font.applied") else t["sub"]),
        ]:
            W.chip(box, txt, color).pack(side="left", padx=(0, 8))

        # cartões de atalho
        grid = ctk.CTkFrame(wrap, fg_color="transparent")
        grid.pack(fill="x")
        for i, (key, icon, title, desc) in enumerate(QUICK):
            card = W.Card(grid)
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")
            grid.grid_columnconfigure(i % 2, weight=1)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=16)
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(top, text=icon, font=W.fnt(26)).pack(side="left")
            ctk.CTkLabel(top, text=" " + title, font=W.fnt(16, "bold"),
                         text_color=t["text"]).pack(side="left")
            ctk.CTkLabel(inner, text=desc, font=W.fnt(12), text_color=t["sub"], anchor="w",
                         justify="left", wraplength=380).pack(fill="x", pady=(6, 12))
            W.primary_button(inner, "Abrir  →", lambda k=key: self.mw.go(k), width=110).pack(anchor="w")

        # toggles rápidos
        quick = ctk.CTkFrame(wrap, fg_color=t["surface"], corner_radius=14)
        quick.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(quick, text="⚡ Liga/desliga rápido", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w", padx=16, pady=(12, 2))
        row = ctk.CTkFrame(quick, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))

        def mk_toggle(parent, label, desc, key):
            fr = ctk.CTkFrame(parent, fg_color=t["card"], corner_radius=12)
            fr.pack(side="left", expand=True, fill="x", padx=6)
            on = bool(config.get(key))
            sw_row = ctk.CTkFrame(fr, fg_color="transparent")
            sw_row.pack(fill="x", padx=14, pady=12)
            ctk.CTkLabel(sw_row, text=f"{label}\n{desc}", font=W.fnt(12), text_color=t["sub"],
                         justify="left", anchor="w").pack(side="left")

            def toggle():
                config.set(key, bool(var.get()))
                if self.app.overlay:
                    self.app.overlay.update_state()
                self.app.after(250, lambda: self.mw.show("home"))

            var = tk.BooleanVar(value=on)
            ctk.CTkSwitch(sw_row, text="", variable=var, progress_color=t["accent"],
                          command=toggle).pack(side="right")

        mk_toggle(row, "✨ Efeitos de clique", "ativados globalmente", "fx.click_enabled")
        mk_toggle(row, "🌈 Trilha do mouse", "rastro animado", "fx.trail_enabled")
