"""Página Pacotes de Ícones: muda os ícones da interface do app + importe os seus."""
from __future__ import annotations

import customtkinter as ctk

from ...core import config, iconpacks
from .. import widgets as W

SAMPLE_KEYS = ["home", "mouse", "click", "trail", "font", "icons", "settings"]


class IconPacksPage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 10))

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x")
        W.section_header(top, "🎨", "Pacotes de Ícones",
                         "Personalize os ícones da interface do Custom MF. Importe o seu pacote "
                         "(.zip ou pasta) com imagens PNG nomeadas: home, mouse, click, trail, "
                         "font, icons, settings…").pack(side="left", fill="x", expand=True)
        W.ghost_button(top, "📂 Importar pacote…", self._import).pack(side="right", pady=(0, 8))

        active = iconpacks.get_active()["name"]
        packs = iconpacks.list_packs()
        for name, data in packs.items():
            is_active = name == active
            card = W.Card(wrap)
            card.pack(fill="x", pady=7)
            box = ctk.CTkFrame(card, fg_color="transparent")
            box.pack(fill="x", padx=16, pady=12)

            left = ctk.CTkFrame(box, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            head = ctk.CTkFrame(left, fg_color="transparent")
            head.pack(fill="x")
            ctk.CTkLabel(head, text=name, font=W.fnt(14, "bold"),
                         text_color=t["text"]).pack(side="left")
            if is_active:
                W.chip(head, "ativo", t["success"]).pack(side="left", padx=10)
            icons_row = ctk.CTkFrame(left, fg_color="transparent")
            icons_row.pack(fill="x", pady=(6, 0))
            for k in SAMPLE_KEYS:
                glyph = data["glyphs"].get(k, "•")
                ctk.CTkLabel(icons_row, text=glyph, font=W.fnt(20), width=40,
                             text_color=t["text"]).pack(side="left")

            if not is_active:
                W.primary_button(box, "Aplicar", lambda n=name: self._apply(n), width=110
                                 ).pack(side="right")

        help_card = W.Card(wrap)
        help_card.pack(fill="x", pady=(12, 0))
        hbox = ctk.CTkFrame(help_card, fg_color="transparent")
        hbox.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(hbox, text="Como criar o seu pacote", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        ctk.CTkLabel(hbox,
                     text="1. Crie uma pasta com imagens PNG de 64×64 (ou mais) nomeadas assim:\n"
                          "     home.png · mouse.png · click.png · trail.png · font.png · icons.png · settings.png\n"
                          "2. Compacte a pasta em um .zip\n"
                          "3. Clique em “Importar pacote…” e escolha o arquivo\n\n"
                          "Dá pra misturar emojis (no pack.json) com PNGs — os PNGs têm prioridade.",
                     font=W.fnt(12), text_color=t["sub"], justify="left").pack(anchor="w", pady=(6, 0))

    def _apply(self, name):
        config.set("theme.icon_pack", name)
        self.app.after(120, self.mw.rebuild)

    def _import(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.app, title="Importar pacote de ícones",
            filetypes=[("Pacote de ícones", "*.zip"), ("Todos", "*.*")])
        if not path:
            return
        try:
            name = iconpacks.import_zip(path)
        except Exception as e:
            name = None
            err = str(e)
        if name:
            config.set("theme.icon_pack", name)
            self.app.after(120, self.mw.rebuild)
        else:
            from tkinter import messagebox
            messagebox.showerror("Importar", "Não achei ícones válidos nesse zip.\n"
                                 "Use PNGs nomeados (home.png, mouse.png…) ou um pack.json.",
                                 parent=self.app)
