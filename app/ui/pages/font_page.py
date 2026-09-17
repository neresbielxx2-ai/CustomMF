"""Página Fonte do Sistema: trocar a fonte do Windows 10/11 e instalar .ttf/.otf."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ...core import config, fonts
from .. import widgets as W


class FontPage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()
        self.families = fonts.installed_families()

    def build(self, parent):
        t = self.t
        wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=30, pady=(22, 10))

        W.section_header(wrap, "🔤", "Fonte do Sistema",
                         "Muda a fonte dos textos do Windows 10 e 11 (menus, janelas, explorer…). "
                         "Pedirá permissão de administrador e a troca aparece por completo após "
                         "sair da sessão.").pack(fill="x")

        cur = fonts.current_substitute()
        if cur:
            W.chip(wrap, f"em uso: {cur}", t["accent"]).pack(anchor="w", pady=(0, 10))

        # escolha
        card = W.Card(wrap)
        card.pack(fill="x", pady=(0, 14))
        box = ctk.CTkFrame(card, fg_color="transparent")
        box.pack(fill="x", padx=16, pady=14)
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Fonte:", font=W.fnt(13, "bold"), text_color=t["text"]).pack(side="left")
        self.combo = ctk.CTkComboBox(row, values=self.families, width=280, height=32,
                                     font=W.fnt(13), dropdown_font=W.fnt(12),
                                     button_color=t["accent"], button_hover_color=t["button_hover"],
                                     fg_color=t["surface"], border_color=t["border"])
        self.combo.set(config.get("font.applied") or "Segoe UI")
        self.combo.pack(side="left", padx=12)
        W.ghost_button(row, "🔄 Atualizar lista", self._refresh).pack(side="left", padx=4)
        W.ghost_button(row, "📥 Instalar fonte do arquivo…", self._install_file).pack(side="left", padx=4)
        ctk.CTkLabel(box, text="Dica: pode digitar o nome da fonte instalada ou instalar um .ttf/.otf seu.",
                     font=W.fnt(11), text_color=t["sub"]).pack(anchor="w", pady=(8, 0))

        # preview
        pv = W.Card(wrap)
        pv.pack(fill="x", pady=(0, 14))
        pvbox = ctk.CTkFrame(pv, fg_color="transparent")
        pvbox.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(pvbox, text="Pré-visualização", font=W.fnt(13, "bold"),
                     text_color=t["text"]).pack(anchor="w")
        self.preview_lbl = ctk.CTkLabel(pvbox, text="O rato roeu a roupa do rei de Roma 0123456789",
                                        font=ctk.CTkFont(family=self.combo.get(), size=20),
                                        text_color=t["text"], wraplength=700, justify="left")
        self.preview_lbl.pack(fill="x", pady=(8, 2))
        self.preview2 = ctk.CTkLabel(pvbox, text="A B C d e f g — Configurações, Arquivos, Pesquisar…",
                                     font=ctk.CTkFont(family=self.combo.get(), size=14),
                                     text_color=t["sub"], wraplength=700, justify="left")
        self.preview2.pack(fill="x", pady=(0, 6))
        self.combo.configure(command=self._update_preview)

        # aplicar
        actions = W.Card(wrap)
        actions.pack(fill="x")
        abox = ctk.CTkFrame(actions, fg_color="transparent")
        abox.pack(fill="x", padx=16, pady=14)
        W.primary_button(abox, "✅  Aplicar ao Windows", self._apply, width=200).pack(side="left")
        W.danger_button(abox, "↩ Restaurar Segoe UI (padrão)", self._reset).pack(side="left", padx=10)
        self.status = ctk.CTkLabel(abox, text="", font=W.fnt(12), text_color=t["sub"],
                                   wraplength=520, justify="left")
        self.status.pack(fill="x", pady=(10, 0))

    def _update_preview(self, _=None):
        fam = self.combo.get()
        try:
            self.preview_lbl.configure(font=ctk.CTkFont(family=fam, size=20))
            self.preview2.configure(font=ctk.CTkFont(family=fam, size=14))
        except Exception:
            pass

    def _refresh(self):
        self.families = fonts.installed_families()
        self.combo.configure(values=self.families)

    def _install_file(self):
        path = filedialog.askopenfilename(
            parent=self.app, title="Escolha uma fonte (.ttf / .otf)",
            filetypes=[("Fontes", "*.ttf *.otf *.ttc"), ("Todos", "*.*")])
        if not path:
            return

        def work():
            return fonts.install_user_font(path)

        self.status.configure(text="instalando fonte…", text_color=self.t["sub"])
        W.bg_call(self.app, work,
                  on_done=lambda fam: self._after_install(fam),
                  on_error=lambda e: self.status.configure(
                      text=f"erro ao instalar: {e}", text_color=self.t["danger"]))

    def _after_install(self, fam):
        self._refresh()
        self.combo.set(fam)
        self._update_preview()
        self.status.configure(text=f"Fonte “{fam}” instalada! Agora clique em Aplicar ao Windows.",
                              text_color=self.t["success"])

    def _apply(self):
        fam = self.combo.get().strip()
        if not fam:
            return
        if not messagebox.askyesno(
                "Aplicar fonte ao Windows",
                f"Aplicar “{fam}” como fonte do sistema?\n\n"
                "• Vai pedir permissão de administrador (UAC)\n"
                "• A troca aparece por completo depois de sair da sessão\n"
                "• Você pode voltar ao padrão a qualquer momento",
                parent=self.app):
            return
        self.status.configure(text="aplicando… (confirme o aviso do Windows)", text_color=self.t["sub"])

        def work():
            ok, msg = fonts.apply_system_font(fam)
            return ok, msg

        W.bg_call(self.app, work,
                  on_done=lambda r: self._after_apply(r),
                  on_error=lambda e: self.status.configure(text=f"erro: {e}",
                                                           text_color=self.t["danger"]))

    def _after_apply(self, result):
        ok, msg = result
        config.set("font.applied", self.combo.get().strip() if ok else config.get("font.applied"))
        self.status.configure(text=msg, text_color=self.t["success"] if ok else self.t["danger"])

    def _reset(self):
        self.status.configure(text="restaurando…", text_color=self.t["sub"])

        def work():
            return fonts.reset_system_font()

        W.bg_call(self.app, work,
                  on_done=lambda r: (config.set("font.applied", ""),
                                     self.status.configure(
                                         text=r[1],
                                         text_color=self.t["success"] if r[0] else self.t["danger"])),
                  on_error=lambda e: self.status.configure(text=f"erro: {e}",
                                                           text_color=self.t["danger"]))
