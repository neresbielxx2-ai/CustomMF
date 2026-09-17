"""Página Mouse: pacotes de cursor, cursor por imagem, importar e restaurar."""
from __future__ import annotations

import queue
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from ...core import config, cursors, downloader, paths
from .. import widgets as W

PREVIEW_PX = 60


class MousePage:
    def __init__(self, app, mw):
        self.app = app
        self.mw = mw
        self.t = W.T()
        self._imgs = []
        self._custom_img = None
        self._custom_path = ""
        self._hotspot = (0.0, 0.08)
        self._size = 34
        self._also_hand = tk.BooleanVar(value=False)
        self._dl_status = {}

    # ---------------------------------------------------------------- UI

    def build(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(22, 6))
        W.section_header(top, "🖱️", "Mouse",
                         "Troque o cursor do sistema na hora (sem reiniciar). Antes de aplicar, "
                         "salvamos seus cursores atuais — dá pra voltar quando quiser.").pack(side="left", fill="x", expand=True)
        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.pack(side="right")
        W.ghost_button(btns, "📂 Importar .zip", self._import_zip).pack(side="left", padx=4)
        W.danger_button(btns, "↩ Padrão do Windows", self._restore_default).pack(side="left", padx=4)

        self.grid_wrap = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=380)
        self.grid_wrap.pack(fill="both", expand=True, padx=24, pady=(4, 8))
        self._render_packs()

        # -------- cursor personalizado por imagem
        card = W.Card(parent)
        card.pack(fill="x", padx=24, pady=(0, 20))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(left, text="Sua imagem como cursor", font=W.fnt(13, "bold"),
                     text_color=self.t["text"]).pack(anchor="w")
        self.preview = tk.Canvas(left, width=140, height=140, bg=self.t["bg_deep"],
                                 highlightthickness=1, highlightbackground=self.t["border"])
        self.preview.pack(pady=8)
        self.preview.bind("<Button-1>", self._pick_hotspot)
        ctk.CTkLabel(left, text="clique na prévia para definir a ponta (hotspot)",
                     font=W.fnt(10), text_color=self.t["sub"]).pack()

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True)
        W.primary_button(right, "🖼️  Escolher imagem…", self._choose_image).pack(anchor="w")
        self.file_lbl = ctk.CTkLabel(right, text="nenhuma imagem escolhida", font=W.fnt(11),
                                     text_color=self.t["sub"], anchor="w")
        self.file_lbl.pack(anchor="w", pady=(4, 10))
        self.size_row = W.SliderRow(right, "Tamanho do cursor", 16, 96, self._size,
                                    fmt=lambda v: f"{int(v)} px", steps=80,
                                    command=self._on_size)
        self.size_row.pack(fill="x", pady=(0, 6))
        hand_row = ctk.CTkFrame(right, fg_color="transparent")
        hand_row.pack(fill="x", pady=(0, 10))
        ctk.CTkSwitch(hand_row, text="usar também como mão (links)", variable=self._also_hand,
                      progress_color=self.t["accent"], font=W.fnt(12)).pack(side="left")
        self.apply_custom_btn = W.primary_button(right, "✅  Aplicar meu cursor",
                                                 self._apply_custom, state="disabled")
        self.apply_custom_btn.pack(anchor="w")
        self.custom_status = ctk.CTkLabel(right, text="", font=W.fnt(11), text_color=self.t["sub"])
        self.custom_status.pack(anchor="w", pady=(4, 0))
        if config.get("cursor.custom_image"):
            try:
                self._load_custom_image(config.get("cursor.custom_image"))
            except Exception:
                pass

    # ------------------------------------------------------------- packs

    def _render_packs(self):
        for wdg in self.grid_wrap.winfo_children():
            wdg.destroy()
        self._imgs.clear()
        packs = cursors.scan_packs()
        by_name = {p["name"].lower(): p for p in packs}
        active = (cursors.current_scheme() or "").lower()

        cards = []
        for p in packs:
            cards.append(("pack", p))
        for kd in cursors.KNOWN_DOWNLOADS:
            if kd["title"].lower() not in by_name:
                cards.append(("dl", kd))
        cards.append(("default", None))

        cols = 3
        for i, (kind, item) in enumerate(cards):
            card = W.Card(self.grid_wrap)
            card.grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="nsew")
            self.grid_wrap.grid_columnconfigure(i % cols, weight=1)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=12)

            if kind == "default":
                ctk.CTkLabel(inner, text="🪟", font=W.fnt(34)).pack()
                ctk.CTkLabel(inner, text="Windows Padrão", font=W.fnt(13, "bold"),
                             text_color=self.t["text"]).pack()
                ctk.CTkLabel(inner, text="volta aos cursores originais", font=W.fnt(10),
                             text_color=self.t["sub"]).pack(pady=(0, 8))
                is_default = active in ("", "windows padrão")
                btn = W.primary_button(inner, "✔ Ativo" if is_default else "Aplicar",
                                       self._restore_default if not is_default else (lambda: None),
                                       width=120, state="normal" if not is_default else "disabled")
                btn.pack()
                continue

            if kind == "dl":
                kd = item
                ctk.CTkLabel(inner, text="⬇️", font=W.fnt(34)).pack()
                ctk.CTkLabel(inner, text=kd["title"], font=W.fnt(13, "bold"),
                             text_color=self.t["text"]).pack()
                st = ctk.CTkLabel(inner, text="não instalado", font=W.fnt(10),
                                  text_color=self.t["sub"])
                st.pack(pady=(0, 6))
                self._dl_status[kd["key"]] = st
                W.ghost_button(inner, "Baixar", lambda k=kd: self._download_one(k), width=120).pack()
                continue

            pack = item
            is_active = pack["name"].lower() == active
            if pack.get("arrow") is not None:
                try:
                    img = pack["arrow"].copy()
                    img.thumbnail((PREVIEW_PX * 2, PREVIEW_PX * 2), Image.LANCZOS)
                    cimg = ctk.CTkImage(img, size=(img.width, img.height))
                    self._imgs.append(cimg)
                    ctk.CTkLabel(inner, image=cimg, text="").pack(pady=2)
                except Exception:
                    ctk.CTkLabel(inner, text="🖱️", font=W.fnt(34)).pack()
            else:
                ctk.CTkLabel(inner, text="🖱️", font=W.fnt(34)).pack()
            ctk.CTkLabel(inner, text=pack["name"], font=W.fnt(13, "bold"),
                         text_color=self.t["text"], wraplength=180).pack()
            ctk.CTkLabel(inner, text=f"{len(pack['roles'])} cursores", font=W.fnt(10),
                         text_color=self.t["sub"]).pack(pady=(0, 6))
            if is_active:
                W.primary_button(inner, "✔ Ativo", (lambda: None), width=120,
                                 state="disabled").pack()
            else:
                W.primary_button(inner, "Aplicar",
                                 lambda p=pack: self._apply_pack(p), width=120).pack()

    def _apply_pack(self, pack):
        try:
            cursors.apply_pack(pack)
            self._toast(f"Cursor “{pack['name']}” aplicado! 🎉")
            self.app.after(150, lambda: self.mw.show("mouse"))
        except Exception as e:
            self._toast(f"Falha ao aplicar: {e}", err=True)

    def _restore_default(self):
        try:
            cursors.restore_windows_default()
            self.app.after(150, lambda: self.mw.show("mouse"))
        except Exception as e:
            self._toast(f"Falha ao restaurar: {e}", err=True)

    def _import_zip(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(parent=self.app, title="Escolha um pacote de cursores",
                                          filetypes=[("Pacote de cursores", "*.zip")])
        if not path:
            return
        try:
            names = cursors.install_from_zip(path)
            self._toast(f"Pacote importado: {', '.join(names) or '?'}")
            self.app.after(150, lambda: self.mw.show("mouse"))
        except Exception as e:
            self._toast(f"Não foi possível importar: {e}", err=True)

    def _download_one(self, kd):
        st = self._dl_status.get(kd["key"])
        if st:
            st.configure(text="baixando…", text_color=self.t["accent"])
        q: queue.Queue = queue.Queue()

        def work():
            dl = downloader.Downloader([{**kd, "weight": 1}], q)
            dl.run()

        W.bg_call(self.grid_wrap, work,
                  on_done=lambda _: None,
                  on_error=lambda e: st and st.configure(text=f"erro: {e}", text_color=self.t["danger"]))

        def poll():
            try:
                ev, *rest = q.get_nowait()
                if ev == "done":
                    self._toast(f"{kd['title']} instalado!")
                    self.mw.show("mouse")
                    return
                if ev == "item_state" and rest[1] == "err":
                    st.configure(text=f"erro: {rest[2][:60]}", text_color=self.t["danger"])
                    return
            except queue.Empty:
                pass
            try:
                if self.grid_wrap.winfo_exists():
                    self.grid_wrap.after(80, poll)
            except Exception:
                pass

        self.grid_wrap.after(80, poll)

    # ------------------------------------------------------- imagem→cursor

    def _choose_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.app, title="Escolha uma imagem para o cursor",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.cur *.ico"), ("Todos", "*.*")])
        if not path:
            return
        self._load_custom_image(path)

    def _load_custom_image(self, path):
        from ...core import curio
        img, _ = curio.read_cursor_file(path)
        self._custom_img = img
        self._custom_path = path
        self.file_lbl.configure(text=Path(path).name)
        self.apply_custom_btn.configure(state="normal")
        self._draw_preview()

    def _on_size(self, v):
        self._size = int(v)
        self._draw_preview()

    def _draw_preview(self):
        c = self.preview
        if self._custom_img is None:
            c.delete("all")
            c.create_text(70, 60, text="🖼️", font=("Segoe UI Emoji", 28), fill=self.t["sub"])
            c.create_text(70, 100, text="escolha uma imagem", font=("Segoe UI", 10), fill=self.t["sub"])
            return
        img = self._custom_img.copy()
        img.thumbnail((120, 120), Image.LANCZOS)
        self._ph = ctk.CTkImage(img, size=(img.width, img.height))
        self._imgs.append(self._ph)
        c.delete("all")
        c.create_image(70, 70, image=self._ph)
        hx = int(self._hotspot[0] * img.width)
        hy = int(self._hotspot[1] * img.height)
        x0 = 70 - img.width // 2
        y0 = 70 - img.height // 2
        c.create_oval(x0 + hx - 5, y0 + hy - 5, x0 + hx + 5, y0 + hy + 5,
                      outline="#FF5C7A", width=2)
        c.create_line(x0 + hx - 9, y0 + hy, x0 + hx + 9, y0 + hy, fill="#FF5C7A", width=1)
        c.create_line(x0 + hx, y0 + hy - 9, x0 + hx, y0 + hy + 9, fill="#FF5C7A", width=1)

    def _pick_hotspot(self, ev):
        if self._custom_img is None:
            return
        img = self._custom_img.copy()
        img.thumbnail((120, 120), Image.LANCZOS)
        x0 = 70 - img.width // 2
        y0 = 70 - img.height // 2
        px = max(0, min(img.width - 1, ev.x - x0))
        py = max(0, min(img.height - 1, ev.y - y0))
        self._hotspot = (px / img.width, py / img.height)
        self._draw_preview()

    def _apply_custom(self):
        if self._custom_path == "":
            return
        try:
            self.apply_custom_btn.configure(state="disabled", text="aplicando…")
            cursors.apply_image_cursor(self._custom_path, self._size, self._hotspot,
                                       self._also_hand.get())
            self._toast("Seu cursor personalizado foi aplicado! 🎉")
            self.app.after(150, lambda: self.mw.show("mouse"))
        except Exception as e:
            self.apply_custom_btn.configure(state="normal", text="✅  Aplicar meu cursor")
            self.custom_status.configure(text=f"erro: {e}", text_color=self.t["danger"])

    def _toast(self, msg, err=False):
        top = ctk.CTkToplevel(self.app)
        top.withdraw()
        top.overrideredirect(True)
        t = self.t
        fr = ctk.CTkFrame(top, corner_radius=12, fg_color=t["danger"] if err else t["accent"])
        fr.pack(padx=2, pady=2)
        ctk.CTkLabel(fr, text=msg, font=W.fnt(12, "bold"),
                     text_color=t["on_accent"]).pack(padx=16, pady=10)
        sw, sh = self.app.winfo_screenwidth(), self.app.winfo_screenheight()
        top.update_idletasks()
        w, h = top.winfo_reqwidth(), top.winfo_reqheight()
        top.geometry(f"+{sw - w - 30}+{sh - h - 60}")
        top.deiconify()
        top.after(2600, top.destroy)
