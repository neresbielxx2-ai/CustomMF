"""Janela principal: barra lateral com navegação + páginas."""
from __future__ import annotations

import customtkinter as ctk

from .. import __version__
from ..core import config, iconpacks, theme
from . import widgets as W
from .pages.click_page import ClickPage
from .pages.font_page import FontPage
from .pages.home import HomePage
from .pages.iconpacks_page import IconPacksPage
from .pages.mouse_page import MousePage
from .pages.settings_page import SettingsPage
from .pages.trails_page import TrailsPage

NAV = [
    ("home", "Início", "home"),
    ("mouse", "Mouse", "mouse"),
    ("click", "Efeitos de Clique", "click"),
    ("trail", "Trilhas", "trail"),
    ("font", "Fonte do Sistema", "font"),
    ("icons", "Pacotes de Ícones", "icons"),
    ("settings", "Configurações", "settings"),
]

PAGES = {
    "home": HomePage,
    "mouse": MousePage,
    "click": ClickPage,
    "trail": TrailsPage,
    "font": FontPage,
    "icons": IconPacksPage,
    "settings": SettingsPage,
}


class MainWindow:
    def __init__(self, app, overlay):
        self.app = app
        self.overlay = overlay
        self.current = "home"
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._imgs: list = []
        self.build()

    # ------------------------------------------------------------ build

    def build(self):
        t = W.T()
        self.wrap = ctk.CTkFrame(self.app, fg_color=t["bg"], corner_radius=0)
        self.wrap.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.wrap, width=232, corner_radius=0, fg_color=t["surface"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        head = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(20, 6))
        ctk.CTkLabel(head, text=iconpacks.glyph("mouse", "🖱️") + "  Custom MF",
                     font=W.fnt(19, "bold"), text_color=t["text"]).pack(side="left")
        ctk.CTkLabel(self.sidebar, text="personalize seu Windows", font=W.fnt(10),
                     text_color=t["sub"], anchor="w").pack(fill="x", padx=22)

        ctk.CTkFrame(self.sidebar, height=1, fg_color=t["border"]).pack(fill="x", padx=14, pady=10)

        self.nav_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_box.pack(fill="x", padx=10)
        for key, label, icon_key in NAV:
            self._nav_btns[key] = self._nav_button(self.nav_box, key, label, icon_key)

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=14, pady=14)
        theme_txt = "☀️  Tema claro" if t["dark"] else "🌙  Tema escuro"
        W.ghost_button(bottom, theme_txt, self.toggle_theme).pack(fill="x")
        ctk.CTkLabel(bottom, text=f"versão {__version__}", font=W.fnt(10),
                     text_color=t["sub"]).pack(pady=(8, 0))

        self.container = ctk.CTkFrame(self.wrap, fg_color="transparent", corner_radius=0)
        self.container.pack(side="left", fill="both", expand=True)
        self.show(self.current)

    def _nav_button(self, parent, key, label, icon_key) -> ctk.CTkButton:
        t = W.T()
        active = key == self.current
        glyph = iconpacks.glyph(icon_key, "•")
        txt = f" {glyph}   {label}"
        btn = ctk.CTkButton(
            parent, text=txt, anchor="w", height=42, corner_radius=10,
            font=W.fnt(13, "bold" if active else "normal"),
            fg_color=t["accent"] if active else "transparent",
            hover_color=t["accent"] if active else t["hover_soft"],
            text_color=t["on_accent"] if active else t["sub"],
            command=lambda: self.show(key))
        btn.pack(fill="x", pady=2)
        return btn

    # ------------------------------------------------------------ navegação

    def show(self, key: str):
        self.current = key
        t = W.T()
        for k, btn in self._nav_btns.items():
            active = k == key
            btn.configure(fg_color=t["accent"] if active else "transparent",
                          text_color=t["on_accent"] if active else t["sub"],
                          font=W.fnt(13, "bold" if active else "normal"))
        for wdg in self.container.winfo_children():
            wdg.destroy()
        page = PAGES[key](self.app, self)
        page.build(self.container)

    def rebuild(self):
        """Reconstrói tudo (após trocar tema/pacote de ícones)."""
        try:
            self.wrap.destroy()
        except Exception:
            pass
        ctk.set_appearance_mode(theme.ctk_appearance())
        self.app.configure(fg_color=W.T()["bg"])
        self._nav_btns.clear()
        self.build()

    def toggle_theme(self):
        cur = config.get("theme.appearance", "dark")
        config.set("theme.appearance", "light" if cur != "light" else "dark")
        self.app.after(120, self.rebuild)

    # ------------------------------------------------- helpers p/ páginas

    def go(self, key: str):
        self.show(key)
