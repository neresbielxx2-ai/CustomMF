"""Página Configurações: aparência, cores do tema, dados e sobre."""
from __future__ import annotations

import customtkinter as ctk

from ... import __version__
from ...core import config, paths, theme
from .. import widgets as W


class SettingsPage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 10))

        W.section_header(wrap, "⚙️", "Configurações",
                         "Tema, cores e dados do app. O fundo é escuro por padrão — mas você "
                         "manda em tudo por aqui.").pack(fill="x")

        # ---------------- aparência
        card = W.Card(wrap)
        card.pack(fill="x", pady=(0, 14))
        box = ctk.CTkFrame(card, fg_color="transparent")
        box.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(box, text="Modo de cor", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        cur = config.get("theme.appearance", "dark")
        seg = ctk.CTkSegmentedButton(box, values=["🌙 Escuro", "☀️ Claro", "💻 Sistema"],
                                     font=W.fnt(12), height=34, corner_radius=10,
                                     selected_color=t["accent"], selected_hover_color=t["button_hover"],
                                     unselected_color=t["hover_soft"], unselected_hover_color=t["border"],
                                     fg_color=t["surface"], text_color=t["text"],
                                     command=self._set_appearance)
        seg.set({"dark": "🌙 Escuro", "light": "☀️ Claro", "system": "💻 Sistema"}.get(cur, "🌙 Escuro"))
        seg.pack(anchor="w", pady=(8, 12))

        ctk.CTkLabel(box, text="Tom do fundo", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        tones = theme.DARK_TONES if t["dark"] else theme.LIGHT_TONES
        labels = {"profundo": "Profundo", "padrao": "Padrão", "suave": "Suave",
                  "branco": "Branco", "gelo": "Gelo"}
        tone_row = ctk.CTkFrame(box, fg_color="transparent")
        tone_row.pack(fill="x", pady=6)
        cur_tone = config.get("theme.bg_tone", "padrao")
        for key, hexc in tones.items():
            sel = key == cur_tone
            b = ctk.CTkButton(tone_row, text=("● " if sel else "○ ") + labels.get(key, key),
                              width=120, height=34, corner_radius=10, font=W.fnt(12, "bold"),
                              fg_color=t["accent"] if sel else t["hover_soft"],
                              hover_color=t["border"],
                              text_color=t["on_accent"] if sel else t["text"],
                              command=lambda k=key: self._set_tone(k))
            b.pack(side="left", padx=(0, 8))

        # preview das cores
        self._preview(box)

        # ---------------- cor de destaque
        acc = W.Card(wrap)
        acc.pack(fill="x", pady=(0, 14))
        abox = ctk.CTkFrame(acc, fg_color="transparent")
        abox.pack(fill="x", padx=16, pady=14)
        W.ColorRow(abox, "Cor de destaque (menus, destaques, barras)",
                   value=config.get("theme.accent", "#7C5CFF"),
                   on_change=self._set_accent).pack(fill="x", pady=(0, 10))
        W.ColorRow(abox, "Cor dos botões (em branco = usar a de destaque)",
                   value=config.get("theme.button_color") or config.get("theme.accent", "#7C5CFF"),
                   on_change=self._set_button).pack(fill="x")
        W.ghost_button(abox, "↩ Usar destaque nos botões",
                       lambda: self._set_button(None)).pack(anchor="w", pady=(8, 0))

        # ---------------- dados
        data_card = W.Card(wrap)
        data_card.pack(fill="x", pady=(0, 14))
        dbox = ctk.CTkFrame(data_card, fg_color="transparent")
        dbox.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(dbox, text="Dados", font=W.fnt(13, "bold"), text_color=t["text"]).pack(anchor="w")
        row = ctk.CTkFrame(dbox, fg_color="transparent")
        row.pack(fill="x", pady=8)
        W.ghost_button(row, "📁 Abrir pasta do app", self._open_data).pack(side="left", padx=(0, 8))
        W.ghost_button(row, "⬇️ Baixar componentes de novo", self._redo_download).pack(side="left")

        # ---------------- sobre
        about = W.Card(wrap)
        about.pack(fill="x")
        ab = ctk.CTkFrame(about, fg_color="transparent")
        ab.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(ab, text=f"Custom MF v{__version__}", font=W.fnt(14, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        ctk.CTkLabel(ab,
                     "Feito para deixar o seu Windows com a sua cara.\n"
                     "Pacotes de cursor: macOS & Bibata & BreezeX — por ful1e5 (licença Apache 2.0).\n"
                     "Seus cursores são sempre salvos antes de qualquer troca. 💜",
                     font=W.fnt(12), text_color=t["sub"], justify="left").pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------ widgets

    def _preview(self, parent):
        t = self.t
        pv = ctk.CTkFrame(parent, corner_radius=12, fg_color=t["surface"],
                          border_width=1, border_color=t["border"])
        pv.pack(fill="x", pady=(10, 0))
        inner = ctk.CTkFrame(pv, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text="Prévia:", font=W.fnt(11, "bold"),
                     text_color=t["sub"]).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=6)
        W.primary_button(row, "Botão", (lambda: None), width=110).pack(side="left")
        W.ghost_button(row, "Secundário", (lambda: None), width=110).pack(side="left", padx=8)
        ctk.CTkLabel(row, text="Texto normal", font=W.fnt(12), text_color=t["text"]).pack(side="left", padx=8)
        ctk.CTkLabel(row, text="destaque", font=W.fnt(12, "bold"), text_color=t["accent"]).pack(side="left")

    # ------------------------------------------------------------ ações

    def _set_appearance(self, label):
        m = {"🌙 Escuro": "dark", "☀️ Claro": "light", "💻 Sistema": "system"}.get(label, "dark")
        config.set("theme.appearance", m)
        self.app.after(120, self.mw.rebuild)

    def _set_tone(self, key):
        config.set("theme.bg_tone", key)
        self.app.after(120, self.mw.rebuild)

    def _set_accent(self, color):
        if color == "rainbow":
            color = "#7C5CFF"
        config.set("theme.accent", color)
        self.app.after(120, self.mw.rebuild)

    def _set_button(self, color):
        if color in (None, "rainbow"):
            config.set("theme.button_color", "")
        else:
            config.set("theme.button_color", color)
        self.app.after(120, self.mw.rebuild)

    def _open_data(self):
        import os
        import subprocess
        path = str(paths.app_data_dir())
        try:
            os.startfile(path)  # Windows
        except Exception:
            try:
                subprocess.Popen(["xdg-open", path])
            except Exception:
                pass

    def _redo_download(self):
        config.set("first_run_done", False)
        from tkinter import messagebox
        messagebox.showinfo(
            "Rebaixar componentes",
            "Na próxima vez que abrir o Custom MF, a tela de download "
            "“Baixando componentes, aguarde…” vai aparecer de novo.",
            parent=self.app)
