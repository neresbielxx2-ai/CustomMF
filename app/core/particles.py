"""Motor de partículas para efeitos de clique e trilhas do mouse.

Independente de toolkit: desenha através de um `Adapter` (no app é um Canvas do
tkinter; nos testes, um gravador). Cores "desvanecem" convergindo para a cor de
fundo transparente — truque que funciona com `-transparentcolor`.
"""
from __future__ import annotations

import colorsys
import math
import random
import time


# ------------------------------------------------------------ utilidades

def hex_rgb(c: str) -> tuple[float, float, float]:
    c = (c or "#FFFFFF").lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except Exception:
        return 255, 255, 255


def rgb_hex(r, g, b) -> str:
    return f"#{max(0, min(255, int(r))):02X}{max(0, min(255, int(g))):02X}{max(0, min(255, int(b))):02X}"


def mix(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = hex_rgb(c1)
    r2, g2, b2 = hex_rgb(c2)
    return rgb_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def rainbow(t: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(t % 1.0, 0.85, 1.0)
    return rgb_hex(r * 255, g * 255, b * 255)


CLICK_TYPES = ["onda", "pulso", "faiscas", "estrelas", "coracoes", "flash", "fogos"]
CLICK_LABELS = {"onda": "🌊  Onda", "pulso": "💠  Pulso", "faiscas": "✨  Faíscas",
                "estrelas": "⭐  Estrelas", "coracoes": "💜  Corações", "flash": "⚡  Flash",
                "fogos": "🎆  Fogos"}
TRAIL_TYPES = ["neon", "arcoiris", "bolhas", "estrelas", "coracoes", "fogo", "po"]
TRAIL_LABELS = {"neon": "💫  Neon", "arcoiris": "🌈  Arco-íris", "bolhas": "🔵  Bolhas",
                "estrelas": "⭐  Estrelas", "coracoes": "💜  Corações", "fogo": "🔥  Fogo",
                "po": "✨  Pó de estrela"}


class Adapter:
    """Interface de desenho. Coordenadas em px."""

    def clear(self): ...
    def w(self) -> int: return 400
    def h(self) -> int: return 300

    def ring(self, cx, cy, r, width, color): ...
    def dot(self, cx, cy, r, color): ...
    def glyph(self, cx, cy, char, size, color): ...
    def line(self, x1, y1, x2, y2, width, color): ...


# ---------------------------------------------------------------- engine

class Engine:
    """Partículas desenhadas a cada `step()`. Reaproveitado por overlay e previews."""

    MAX_PARTICLES = 420

    def __init__(self, adapter: Adapter):
        self.a = adapter
        self.p: list[dict] = []
        self._hue = random.random()

    # ---------------------------------------------------- spawn: cliques

    def click(self, x: float, y: float, cfg: dict, button: int = 1) -> None:
        if not cfg.get("click_enabled"):
            return
        kind = cfg.get("click_type", "onda")
        base = cfg.get("click_color", "#7C5CFF")
        rb = cfg.get("click_rainbow", False)
        size = float(cfg.get("click_size", 1.0))
        dur = float(cfg.get("click_duration", 1.0))
        now = time.monotonic()
        color = None if rb else base
        h0 = self._hue = (self._hue + 0.31) % 1.0

        def col(i=0.0):
            return rainbow(h0 + i) if rb else (color or base)

        if kind == "onda":
            self._add(kind="ring", x=x, y=y, born=now, life=0.55 * dur, color=col(),
                      r0=4 * size, r1=52 * size, w0=4, ease=1)
        elif kind == "pulso":
            self._add(kind="ring", x=x, y=y, born=now, life=0.45 * dur, color=col(),
                      r0=3 * size, r1=44 * size, w0=5, ease=1)
            self._add(kind="ring", x=x, y=y, born=now + 0.13 * dur, life=0.45 * dur, color=col(0.18),
                      r0=3 * size, r1=34 * size, w0=3, ease=1)
        elif kind == "faiscas":
            for i in range(14):
                ang = random.uniform(0, math.tau)
                sp = random.uniform(90, 210) * size
                self._add(kind="spark", x=x, y=y, vx=math.cos(ang) * sp, vy=math.sin(ang) * sp - 40,
                          born=now, life=random.uniform(0.45, 0.8) * dur, color=col(random.uniform(0, .2)),
                          r=random.uniform(1.6, 3.4) * size)
        elif kind == "estrelas":
            for i in range(8):
                ang = (i / 8) * math.tau + random.uniform(-.2, .2)
                dist = random.uniform(22, 46) * size
                self._add(kind="star", x=x + math.cos(ang) * dist * .3, y=y + math.sin(ang) * dist * .3,
                          vx=math.cos(ang) * dist * 2.2, vy=math.sin(ang) * dist * 2.2 - 30,
                          born=now, life=random.uniform(.5, .8) * dur, color=col(i / 8),
                          r=random.uniform(7, 13) * size)
        elif kind == "coracoes":
            for i in range(6):
                self._add(kind="heart", x=x + random.uniform(-14, 14) * size, y=y,
                          vx=random.uniform(-25, 25) * size, vy=random.uniform(-95, -45) * size,
                          born=now, life=random.uniform(.6, .95) * dur, color=col(random.uniform(0, .12)),
                          r=random.uniform(9, 15) * size)
        elif kind == "flash":
            self._add(kind="flash", x=x, y=y, born=now, life=0.32 * dur, color=col(),
                      r1=34 * size)
            self._add(kind="ring", x=x, y=y, born=now, life=0.4 * dur, color=col(),
                      r0=6 * size, r1=30 * size, w0=2, ease=0)
        elif kind == "fogos":
            for wave in range(3):
                base_h = random.random()
                for i in range(10):
                    ang = random.uniform(0, math.tau)
                    sp = random.uniform(60, 150) * size
                    self._add(kind="spark", x=x, y=y, vx=math.cos(ang) * sp, vy=math.sin(ang) * sp,
                              born=now + wave * 0.16 * dur, life=random.uniform(.5, .75) * dur,
                              color=col(base_h + i / 10), r=random.uniform(1.5, 2.8) * size)

    # ------------------------------------------------- spawn: trilhas

    def trail_spawn(self, x: float, y: float, cfg: dict, px: float | None = None, py: float | None = None) -> None:
        if not cfg.get("trail_enabled"):
            return
        kind = cfg.get("trail_type", "neon")
        rb = cfg.get("trail_rainbow", False)
        base = cfg.get("trail_color", "#3DDC97")
        size = float(cfg.get("trail_size", 1.0))
        life = float(cfg.get("trail_duration", 1.0))
        now = time.monotonic()
        h = self._hue = (self._hue + 0.045) % 1.0
        color = rainbow(h) if rb else base

        if kind in ("neon", "arcoiris") and px is not None:
            d = math.hypot(x - px, y - py)
            if d > 90:
                # segmenta retas longas
                steps = int(d // 60) + 1
                for i in range(1, steps + 1):
                    t = i / steps
                    self._add(kind="trail_line", x=px + (x - px) * (t - 1 / steps), y=py + (y - py) * (t - 1 / steps),
                              x2=px + (x - px) * t, y2=py + (y - py) * t,
                              born=now, life=0.55 * life, color=rainbow(h + t * .2) if rb else color,
                              lw=5 * size)
            else:
                self._add(kind="trail_line", x=px, y=py, x2=x, y2=y, born=now, life=0.55 * life,
                          color=color, lw=5 * size)
        elif kind == "bolhas":
            self._add(kind="bubble", x=x + random.uniform(-6, 6) * size, y=y,
                      vx=random.uniform(-8, 8), vy=random.uniform(-34, -16),
                      born=now, life=random.uniform(.6, 1.0) * life, color=color,
                      r=random.uniform(2.5, 6) * size)
        elif kind == "estrelas":
            self._add(kind="star", x=x + random.uniform(-9, 9), y=y + random.uniform(-9, 9),
                      vx=random.uniform(-14, 14), vy=random.uniform(-8, 22),
                      born=now, life=random.uniform(.5, .9) * life, color=color,
                      r=random.uniform(4, 8) * size)
        elif kind == "coracoes":
            self._add(kind="heart", x=x + random.uniform(-8, 8), y=y,
                      vx=random.uniform(-10, 10), vy=random.uniform(-40, -18),
                      born=now, life=random.uniform(.55, .9) * life, color=color,
                      r=random.uniform(7, 11) * size)
        elif kind == "fogo":
            self._add(kind="fire", x=x + random.uniform(-4, 4) * size, y=y,
                      vx=random.uniform(-6, 6), vy=random.uniform(-70, -40) * size,
                      born=now, life=random.uniform(.4, .7) * life,
                      r=random.uniform(4, 8) * size)
        elif kind == "po":
            for i in range(2):
                self._add(kind="dust", x=x + random.uniform(-12, 12), y=y + random.uniform(-12, 12),
                          vx=random.uniform(-12, 12), vy=random.uniform(-20, 8),
                          born=now, life=random.uniform(.4, .8) * life, color=color,
                          r=random.uniform(.8, 2) * size)

    @staticmethod
    def trail_interval_px(density: int) -> float:
        return {1: 56.0, 2: 38.0, 3: 26.0, 4: 16.0, 5: 9.0}.get(int(density), 26.0)

    # ----------------------------------------------------------- step

    def idle(self) -> bool:
        return not self.p

    def clear(self) -> None:
        self.p.clear()
        self.a.clear()

    def _add(self, **p) -> None:
        if len(self.p) >= self.MAX_PARTICLES:
            self.p.pop(0)
        p.setdefault("life", 0.6)
        self.p.append(p)

    def step(self, now: float | None = None, bg: str = "#010203") -> None:
        """Avança 1 quadro: remove expiradas e redesenha tudo."""
        now = now or time.monotonic()
        alive = []
        for p in self.p:
            t = (now - p.get("born", now)) / max(0.001, p["life"])
            if 0 <= t < 1:
                alive.append((p, t))
        self.p = [p for p, _ in alive]
        a = self.a
        a.clear()
        for p, t in alive:
            self._draw(p, t, bg)

    # ---------------------------------------------------------- draw

    def _draw(self, p: dict, t: float, bg: str) -> None:
        a = self.a
        kind = p["kind"]
        color = p.get("color")
        if color is None:
            color = rainbow(t)
        fade = t * t
        col = mix(color, bg, fade)

        if kind == "ring":
            tt = t ** (0.6 if p.get("ease") else 1.0)
            r = p["r0"] + (p["r1"] - p["r0"]) * tt
            lw = max(1, int(p["w0"] * (1 - t) + 1))
            a.ring(p["x"], p["y"], r, lw, col)
        elif kind == "spark":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 260 * dt
            a.dot(p["x"], p["y"], max(0.8, p["r"] * (1 - t)), col)
        elif kind == "star":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            a.glyph(p["x"], p["y"], "✦", max(6, int(p["r"] * (1 - t * .7))), col)
        elif kind == "heart":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            a.glyph(p["x"], p["y"], "♥", max(8, int(p["r"] * (1 - t * .5))), col)
        elif kind == "flash":
            tt = math.sin(t * math.pi)
            a.dot(p["x"], p["y"], max(1, p["r1"] * tt), mix(color, bg, t * .55))
        elif kind == "trail_line":
            lw = max(1, int(p["lw"] * (1 - t)))
            a.line(p["x"], p["y"], p["x2"], p["y2"], lw, col)
            a.dot(p["x2"], p["y2"], lw / 2.2, col)
        elif kind == "bubble":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            a.ring(p["x"], p["y"], max(1, p["r"] * (1 - t * .5)), 2, col)
        elif kind == "fire":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            grad = mix(mix("#FFE066", "#FF4D00", min(1, t * 1.4)), bg, t)
            a.dot(p["x"], p["y"], max(1, p["r"] * (1 - t)), grad)
        elif kind == "dust":
            dt = 0.016
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            tw = 0.5 + 0.5 * math.sin(t * 18)
            a.dot(p["x"], p["y"], max(.6, p["r"] * (1 - t)), mix(color, bg, 1 - tw * (1 - t)))


class CanvasAdapter(Adapter):
    """Desenha num tk.Canvas — todos os itens recebem a tag 'fx'."""

    def __init__(self, canvas):
        self.c = canvas

    def clear(self):
        try:
            self.c.delete("fx")
        except Exception:
            pass

    def w(self):
        return int(self.c.winfo_width() or 400)

    def h(self):
        return int(self.c.winfo_height() or 300)

    def ring(self, cx, cy, r, width, color):
        self.c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width, tags="fx")

    def dot(self, cx, cy, r, color):
        self.c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="", tags="fx")

    def glyph(self, cx, cy, char, size, color):
        self.c.create_text(cx, cy, text=char, fill=color, font=("Segoe UI Symbol", int(size)), tags="fx")

    def line(self, x1, y1, x2, y2, width, color):
        self.c.create_line(x1, y1, x2, y2, fill=color, width=width, capstyle="round", tags="fx")
