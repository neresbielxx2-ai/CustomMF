"""Splash animado de abertura + instalação inicial dos componentes.

Fase 1: animação de logo com anel girando.
Fase 2 (1ª execução): "Baixando componentes, aguarde…" + barra de progresso real.
Fase 3: concluído → abre a janela principal.
"""
from __future__ import annotations

import queue
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from ..core import config, downloader, paths
from . import widgets as W

LOGO_PATH = paths.asset("logo.png")
STATUS_MSGS = ["Iniciando módulos…", "Carregando tema…", "Preparando a mágica…",
               "Ajustando pixels…", "Quase lá…"]


class Splash:
    def __init__(self, app, on_done):
        self.app = app
        self.on_done = on_done
        self.t = W.T()
        self.q: queue.Queue = queue.Queue()
        self.dl: downloader.Downloader | None = None
        self.skip_flag = None
        self._angle = 0
        self._frame = 0
        self._msg_i = 0
        self._done_dl = False

        for wdg in app.winfo_children():
            try:
                wdg.destroy()
            except Exception:
                pass

        self.root = ctk.CTkFrame(app, fg_color=self.t["bg"], corner_radius=0)
        self.root.pack(fill="both", expand=True)

        self.logo_imgs = []
        try:
            base = Image.open(LOGO_PATH).convert("RGBA")
            for size in (96, 108, 118):
                self.logo_imgs.append(ctk.CTkImage(base, size=(size, size)))
        except Exception:
            self.logo_imgs = []

        self.stage = ctk.CTkFrame(self.root, fg_color="transparent")
        self.stage.place(relx=0.5, rely=0.5, anchor="center")

        self.spinner = tk.Canvas(self.stage, width=132, height=132, bg=self.t["bg"],
                                 highlightthickness=0, bd=0)
        self.spinner.pack(pady=(0, 6))
        self.logo_lbl = ctk.CTkLabel(self.stage, text="", image=self.logo_imgs[1] if self.logo_imgs else None)
        self.logo_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.title_lbl = ctk.CTkLabel(self.stage, text="Custom MF", font=W.fnt(30, "bold"),
                                      text_color=self.t["text"])
        self.title_lbl.pack()
        self.sub_lbl = ctk.CTkLabel(self.stage, text=STATUS_MSGS[0], font=W.fnt(13),
                                    text_color=self.t["sub"])
        self.sub_lbl.pack(pady=(2, 0))

        self._animate_logo()
        self._animate_spinner()
        app.after(2100, self._after_intro)

    # ------------------------------------------------------- animações

    def _animate_logo(self):
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        self._frame = (self._frame + 1) % 3
        if self.logo_imgs:
            try:
                self.logo_lbl.configure(image=self.logo_imgs[self._frame])
            except Exception:
                return
        self.root.after(230, self._animate_logo)

    def _animate_spinner(self):
        try:
            if not self.spinner.winfo_exists():
                return
        except Exception:
            return
        self._angle = (self._angle + 12) % 360
        c = self.spinner
        c.delete("all")
        t = self.t
        c.create_oval(10, 10, 122, 122, outline=t["border"], width=3)
        c.create_arc(10, 10, 122, 122, start=self._angle, extent=95,
                     style="arc", outline=t["accent"], width=5)
        self.root.after(33, self._animate_spinner)

    def _rotate_msgs(self):
        """Vai trocando as mensagens de status enquanto a fase 1 estiver na tela."""
        try:
            alive = self.sub_lbl.winfo_exists()
        except Exception:
            alive = False
        if not alive:
            return
        self._msg_i = (self._msg_i + 1) % len(STATUS_MSGS)
        try:
            self.sub_lbl.configure(text=STATUS_MSGS[self._msg_i])
        except Exception:
            return
        self.root.after(700, self._rotate_msgs)

    # --------------------------------------------------------- fases

    def _after_intro(self):
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        first_run = not config.get("first_run_done", False)
        has_packs = any(paths.packs_root().glob("*"))
        if first_run or not has_packs:
            self._build_downloader()
        else:
            self._finish()

    def _build_downloader(self):
        t = self.t
        for wdg in self.stage.winfo_children():
            wdg.destroy()

        ctk.CTkLabel(self.stage, text="Baixando componentes, aguarde…",
                     font=W.fnt(19, "bold"), text_color=t["text"]).pack()
        ctk.CTkLabel(self.stage, text="Estamos deixando tudo pronto na primeira execução.\n"
                                      "Você pode pular e baixar depois, na aba Mouse.",
                     font=W.fnt(12), text_color=t["sub"], justify="center").pack(pady=(2, 14))

        self.bar = ctk.CTkProgressBar(self.stage, width=380, height=12, corner_radius=6,
                                      progress_color=t["accent"], fg_color=t["border"])
        self.bar.set(0)
        self.bar.pack()
        self.pct_lbl = ctk.CTkLabel(self.stage, text="0%", font=W.fnt(13, "bold"),
                                    text_color=t["accent"])
        self.pct_lbl.pack(pady=(4, 0))
        self.detail_lbl = ctk.CTkLabel(self.stage, text="conectando…", font=W.fnt(11),
                                       text_color=t["sub"])
        self.detail_lbl.pack()

        self.items_box = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.items_box.pack(pady=(12, 4))
        self.item_rows = []
        for i, task in enumerate(downloader.DEFAULT_TASKS):
            row = ctk.CTkFrame(self.items_box, fg_color="transparent")
            row.pack(fill="x", pady=1)
            st = ctk.CTkLabel(row, text="○", width=22, font=W.fnt(13, "bold"), text_color=t["sub"])
            st.pack(side="left")
            lb = ctk.CTkLabel(row, text=task["title"], font=W.fnt(12), text_color=t["sub"], anchor="w")
            lb.pack(side="left")
            self.item_rows.append((st, lb))

        self.skip_btn = W.ghost_button(self.stage, "Pular download  »", self._skip)
        self.skip_btn.pack(pady=(12, 0))

        self.dl = downloader.Downloader(downloader.DEFAULT_TASKS, self.q)
        self.skip_flag = self.dl.skip_flag
        self.dl.start()
        self._poll_queue()

    def _poll_queue(self):
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return
        try:
            while True:
                ev, *rest = self.q.get_nowait()
                if ev == "progress":
                    frac, detail = rest
                    self.bar.set(frac)
                    self.pct_lbl.configure(text=f"{int(frac * 100)}%")
                    self.detail_lbl.configure(text=detail)
                elif ev == "item":
                    (idx, title) = rest
                    st, lb = self.item_rows[idx]
                    st.configure(text="●", text_color=self.t["accent"])
                    lb.configure(text=title, text_color=self.t["text"])
                elif ev == "item_state":
                    idx, state, msg = rest
                    st, lb = self.item_rows[idx]
                    if state == "done":
                        st.configure(text="✔", text_color=self.t["success"])
                        lb.configure(text=f"{lb.cget('text')}  ·  ok", text_color=self.t["sub"])
                    elif state == "err":
                        st.configure(text="✖", text_color=self.t["danger"])
                        lb.configure(text=f"{lb.cget('text')}  ·  falhou", text_color=self.t["sub"])
                    else:
                        st.configure(text="○", text_color=self.t["sub"])
                        lb.configure(text=f"{lb.cget('text')}  ·  pulado", text_color=self.t["sub"])
                elif ev == "done":
                    errors = rest[0]
                    self._done_dl = True
                    config.set("first_run_done", True)
                    self._finish(errors)
                    return
        except queue.Empty:
            pass
        self.root.after(60, self._poll_queue)

    def _skip(self):
        if self.skip_flag:
            self.skip_flag.set()

    def _finish(self, errors=0):
        t = self.t
        for wdg in self.stage.winfo_children():
            wdg.destroy()
        ok_canvas = tk.Canvas(self.stage, width=86, height=86, bg=t["bg"], highlightthickness=0)
        ok_canvas.pack(pady=(0, 10))
        pct = {"v": 0}

        title = "Tudo pronto!" if not errors else "Pronto (com avisos)"
        sub = ("Seus componentes favoritos já estão instalados."
               if not errors else
               f"{errors} item(ns) falharam — sem problema, dá pra baixar depois na aba Mouse.")
        ctk.CTkLabel(self.stage, text=title, font=W.fnt(22, "bold"), text_color=t["text"]).pack()
        ctk.CTkLabel(self.stage, text=sub, font=W.fnt(12), text_color=t["sub"],
                     justify="center").pack(pady=(2, 8))

        def draw_check():
            try:
                if not ok_canvas.winfo_exists():
                    return
            except Exception:
                return
            pct["v"] = min(1.0, pct["v"] + 0.07)
            ok_canvas.delete("all")
            extent = int(360 * pct["v"])
            color = t["success"] if not errors else t["warning"]
            ok_canvas.create_arc(12, 12, 74, 74, start=90, extent=-extent, style="arc",
                                 outline=color, width=6)
            if pct["v"] >= 1:
                ok_canvas.create_line(30, 44, 40, 56, 58, 32, fill=color, width=6,
                                      capstyle="round", joinstyle="round")
                self.root.after(450, self._open_main)
                return
            self.root.after(24, draw_check)

        draw_check()

    def _open_main(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        if self.on_done:
            self.on_done()
