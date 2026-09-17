"""Componentes de UI reutilizáveis (cartões, sliders, seletor de cor, threads seguras)."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import colorchooser as _cc

import customtkinter as ctk

from ..core import theme

FONT_FAMILY = "Segoe UI"


def T() -> dict:
    return theme.tokens()


def fnt(size=13, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


# ---------------------------------------------------------------- cartões

class Card(ctk.CTkFrame):
    """Cartão arredondado com borda sutil e (opcional) hover suave."""

    def __init__(self, master, hover: bool = False, **kw):
        t = T()
        super().__init__(master, corner_radius=18, fg_color=t["card"],
                         border_width=1, border_color=t["border"], **kw)
        self._base_color = t["card"]
        self._hover_color = t["card_hover"]
        if hover:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _e):
        try:
            self.configure(fg_color=self._hover_color)
        except Exception:
            pass

    def _on_leave(self, e):
        # ignora Leave gerado ao passar por cima de um widget filho
        try:
            wx, wy = self.winfo_rootx(), self.winfo_rooty()
            ww, wh = self.winfo_width(), self.winfo_height()
            if wx <= e.x_root < wx + ww and wy <= e.y_root < wy + wh:
                return
            self.configure(fg_color=self._base_color)
        except Exception:
            pass


def icon_badge(parent, glyph: str, size: int = 46, font_size: int = 20) -> ctk.CTkFrame:
    """Ícone dentro de um quadrado arredondado suave (destaque da página)."""
    t = T()
    badge = ctk.CTkFrame(parent, width=size, height=size, corner_radius=size // 3,
                         fg_color=t["accent_soft"])
    badge.pack_propagate(False)
    ctk.CTkLabel(badge, text=glyph, font=fnt(font_size), text_color=t["text"]).pack(expand=True)
    return badge


def section_header(parent, icon: str, title: str, subtitle: str | None = None) -> tk.Frame:
    """Cabeçalho de página: badge do ícone + título + descrição."""
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="x", padx=4, pady=(2, 14))
    row = ctk.CTkFrame(box, fg_color="transparent")
    row.pack(fill="x")
    icon_badge(row, icon).pack(side="left", padx=(0, 12))
    texts = ctk.CTkFrame(row, fg_color="transparent")
    texts.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(texts, text=title, font=fnt(21, "bold"), text_color=T()["text"],
                 anchor="w").pack(fill="x")
    if subtitle:
        ctk.CTkLabel(texts, text=subtitle, font=fnt(12), text_color=T()["sub"],
                     anchor="w", justify="left", wraplength=620).pack(fill="x")
    return box


def chip(parent, text: str, color: str) -> ctk.CTkLabel:
    t = T()
    bg = theme.mix(color, t["card"], 0.84) if t["dark"] else theme.mix(color, "#FFFFFF", 0.85)
    return ctk.CTkLabel(parent, text=f" ● {text} ", font=fnt(11),
                        fg_color=bg, corner_radius=10, height=26,
                        text_color=theme.on_color(theme.mix(color, t["card"], 0.2)))


def primary_button(parent, text, command, **kw) -> ctk.CTkButton:
    t = T()
    return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=11,
                         font=fnt(13, "bold"), fg_color=t["button"], hover_color=t["button_hover"],
                         text_color=t["on_button"], **kw)


def ghost_button(parent, text, command, **kw) -> ctk.CTkButton:
    t = T()
    return ctk.CTkButton(parent, text=text, command=command, height=34, corner_radius=11,
                         font=fnt(13), fg_color=t["hover_soft"], hover_color=t["border"],
                         text_color=t["text"], border_width=1, border_color=t["border"], **kw)


def danger_button(parent, text, command, **kw) -> ctk.CTkButton:
    t = T()
    return ctk.CTkButton(parent, text=text, command=command, height=34, corner_radius=11,
                         font=fnt(13), fg_color="transparent", hover_color=t["border"],
                         text_color=t["danger"], border_width=1, border_color=t["danger"], **kw)


def preview_well(parent, size: int = 108) -> ctk.CTkFrame:
    """Moldura arredondada mais escura onde ficam prévias (cursor, imagem…)."""
    t = T()
    well = ctk.CTkFrame(parent, width=size, height=size, corner_radius=16, fg_color=t["bg_deep"],
                        border_width=1, border_color=t["border"])
    well.pack_propagate(False)
    return well


# ---------------------------------------------------------------- linhas

class ToggleRow(ctk.CTkFrame):
    def __init__(self, master, title, desc="", checked=False, command=None, icon=""):
        super().__init__(master, corner_radius=16, fg_color=T()["card"],
                         border_width=1, border_color=T()["border"])
        t = T()
        self.command = command
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=16, pady=14)
        title_txt = f"{icon}  {title}" if icon else title
        self.lbl = ctk.CTkLabel(left, text=title_txt, font=fnt(14, "bold"),
                                text_color=t["text"], anchor="w")
        self.lbl.pack(fill="x")
        if desc:
            ctk.CTkLabel(left, text=desc, font=fnt(11), text_color=t["sub"], anchor="w",
                         justify="left", wraplength=560).pack(fill="x")
        self.var = tk.BooleanVar(value=bool(checked))
        self.sw = ctk.CTkSwitch(self, text="", variable=self.var, width=52,
                                progress_color=t["accent"], button_color=t["surface"],
                                command=self._on)
        self.sw.pack(side="right", padx=16)

    def _on(self):
        if self.command:
            self.command(bool(self.var.get()))

    def set(self, v: bool):
        self.var.set(bool(v))


class SliderRow(ctk.CTkFrame):
    def __init__(self, master, label, from_=0.0, to=1.0, value=1.0, fmt=None, command=None, steps=0):
        super().__init__(master, fg_color="transparent")
        t = T()
        self.fmt = fmt or (lambda v: f"{v:.1f}×")
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=label, font=fnt(12, "bold"), text_color=t["text"],
                     anchor="w").pack(side="left")
        self.val_lbl = ctk.CTkLabel(top, text=f" {self.fmt(value)} ", font=fnt(11, "bold"),
                                    fg_color=t["accent_soft"], text_color=t["accent"],
                                    corner_radius=8, height=22)
        self.val_lbl.pack(side="right")
        self.slider = ctk.CTkSlider(self, from_=from_, to=to, number_of_steps=steps or 200,
                                    height=22, corner_radius=11, border_width=0,
                                    command=self._on, progress_color=t["accent"],
                                    button_color=t["text"], button_hover_color=t["accent"],
                                    fg_color=t["border"])
        self.slider.set(value)
        self.slider.pack(fill="x", pady=(6, 0))
        self._cmd = command

    def _on(self, v):
        self.val_lbl.configure(text=f" {self.fmt(float(v))} ")
        if self._cmd:
            self._cmd(float(v))

    def get(self) -> float:
        return float(self.slider.get())


class ColorRow(ctk.CTkFrame):
    """Paleta de cores + personalizada + modo arco-íris."""

    def __init__(self, master, label="Cor", value="#7C5CFF", rainbow=False,
                 on_change=None, allow_rainbow=True):
        super().__init__(master, fg_color="transparent")
        t = T()
        self.on_change = on_change
        self.rainbow = bool(rainbow)
        ctk.CTkLabel(self, text=label, font=fnt(12, "bold"), text_color=t["text"]).pack(anchor="w")
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=7)
        self.swatches: list[ctk.CTkButton] = []
        for c in theme.SWATCHES:
            b = ctk.CTkButton(row, text="", width=30, height=30, corner_radius=15,
                              fg_color=c, hover_color=theme.lighten(c, 0.1), border_width=2,
                              border_color=t["text"], command=lambda cc=c: self._pick(cc))
            b.pack(side="left", padx=(0, 8))
            self.swatches.append(b)
        ghost_button(row, "Personalizada…", self._custom).pack(side="left", padx=(0, 8))
        if allow_rainbow:
            self.rb_btn = ctk.CTkButton(row, text="🌈 Arco-íris", width=106, height=30,
                                        corner_radius=10, font=fnt(12),
                                        command=self._toggle_rainbow,
                                        fg_color=t["accent"] if self.rainbow else t["hover_soft"],
                                        hover_color=t["border"],
                                        text_color=t["on_accent"] if self.rainbow else t["text"])
            self.rb_btn.pack(side="left")
        self._current = value
        self._highlight(value)

    def _highlight(self, value):
        for b, c in zip(self.swatches, theme.SWATCHES):
            b.configure(border_color=T()["text"],
                        border_width=4 if (not self.rainbow and c.lower() == str(value).lower()) else 2)

    def _pick(self, c):
        self.rainbow = False
        self._current = c
        self._update_rb_btn()
        self._highlight(c)
        self._fire(c)

    def _custom(self):
        c = open_color_dialog(self, self._current)
        if c:
            self.rainbow = False
            self._current = c
            self._update_rb_btn()
            self._highlight(c)
            self._fire(c)

    def _toggle_rainbow(self):
        self.rainbow = not self.rainbow
        self._update_rb_btn()
        self._highlight("")
        self._fire("rainbow")

    def _update_rb_btn(self):
        if hasattr(self, "rb_btn"):
            t = T()
            self.rb_btn.configure(fg_color=t["accent"] if self.rainbow else t["hover_soft"],
                                  text_color=t["on_accent"] if self.rainbow else t["text"])

    def _fire(self, v):
        if self.on_change:
            self.on_change(v)

    def value(self) -> str:
        return "rainbow" if self.rainbow else self._current


def type_button(parent, label, selected, command) -> ctk.CTkButton:
    """Botão de escolha de tipo (efeito/trilha) com estado destacado."""
    t = T()
    return ctk.CTkButton(parent, text=label, height=38, corner_radius=11, font=fnt(12, "bold"),
                         command=command,
                         fg_color=t["accent"] if selected else t["hover_soft"],
                         hover_color=t["button_hover"] if selected else t["border"],
                         text_color=t["on_accent"] if selected else t["text"])


def open_color_dialog(parent, initial="#7C5CFF") -> str | None:
    try:
        res = _cc.askcolor(color=initial, parent=parent, title="Escolha a cor")
    except Exception:
        return None
    if not res or not res[1]:
        return None
    return res[1]


# ------------------------------------------------- threads → UI seguras

def bg_call(widget: tk.Misc, fn, on_done=None, on_error=None):
    """Executa fn() em thread; chama on_done(resultado)/on_error(erro) na UI thread."""
    q: queue.Queue = queue.Queue()

    def worker():
        try:
            q.put(("ok", fn()))
        except Exception as e:  # noqa
            q.put(("err", e))

    threading.Thread(target=worker, daemon=True).start()

    def poll():
        alive = True
        try:
            alive = bool(widget.winfo_exists())
        except Exception:
            alive = False
        if not alive:
            return
        try:
            kind, payload = q.get_nowait()
        except queue.Empty:
            widget.after(60, poll)
            return
        if kind == "ok":
            if on_done:
                on_done(payload)
        else:
            if on_error:
                on_error(payload)

    widget.after(60, poll)
