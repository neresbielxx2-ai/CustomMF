"""Motor de temas: paleta escura/claro com cor de destaque e de botões personalizáveis."""
from __future__ import annotations

import colorsys

from . import config

DARK_TONES = {"profundo": "#0A0C12", "padrao": "#0E1016", "suave": "#161A26"}
LIGHT_TONES = {"branco": "#FBFCFF", "padrao": "#F2F4FA", "gelo": "#E7EBF4"}

SWATCHES = ["#7C5CFF", "#4F8CFF", "#06B6D4", "#22C55E", "#F59E0B", "#FF5C7A", "#EC4899", "#ECEEF8"]


# ---------- utilidades de cor ----------

def _clamp(x: float) -> int:
    return max(0, min(255, int(round(x))))


def hex_to_rgb(c: str) -> tuple[int, int, int]:
    c = c.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except Exception:
        return 124, 92, 255


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{_clamp(r):02X}{_clamp(g):02X}{_clamp(b):02X}"


def mix(c1: str, c2: str, t: float) -> str:
    """Mistura duas cores (t=0 → c1, t=1 → c2)."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def lighten(c: str, f: float = 0.14) -> str:
    r, g, b = hex_to_rgb(c)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    r2, g2, b2 = colorsys.hls_to_rgb(h, min(1, l + f), s)
    return rgb_to_hex(r2 * 255, g2 * 255, b2 * 255)


def darken(c: str, f: float = 0.14) -> str:
    r, g, b = hex_to_rgb(c)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    r2, g2, b2 = colorsys.hls_to_rgb(h, max(0, l - f), s)
    return rgb_to_hex(r2 * 255, g2 * 255, b2 * 255)


def luminance(c: str) -> float:
    r, g, b = hex_to_rgb(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def on_color(c: str) -> str:
    """Cor de texto legível sobre o fundo dado."""
    return "#10121A" if luminance(c) > 150 else "#FFFFFF"


# ---------- tokens ----------

def is_dark() -> bool:
    mode = config.get("theme.appearance", "dark")
    if mode == "system":
        try:
            import darkdetect
            return (darkdetect.theme() or "Dark").lower() == "dark"
        except Exception:
            return True
    return mode != "light"


def tokens() -> dict:
    dark = is_dark()
    tone = config.get("theme.bg_tone", "padrao")
    if dark:
        bg = DARK_TONES.get(tone, DARK_TONES["padrao"])
        accent_cfg = config.get("theme.accent", "#7C5CFF")
        t = {
            "dark": True,
            "bg": bg,
            "bg_deep": darken(bg, 0.25),
            "surface": mix(bg, "#FFFFFF", 0.045),
            "card": mix(bg, "#FFFFFF", 0.07),
            "card_hover": mix(bg, "#FFFFFF", 0.10),
            "border": mix(bg, "#FFFFFF", 0.13),
            "text": "#ECEEF8",
            "sub": mix(bg, "#FFFFFF", 0.55),
            "accent": accent_cfg,
            "success": "#3DDC97",
            "danger": "#FF5C7A",
            "warning": "#F5B84A",
            "shadow": darken(bg, 0.4),
        }
    else:
        bg = LIGHT_TONES.get(tone, LIGHT_TONES["padrao"])
        t = {
            "dark": False,
            "bg": bg,
            "bg_deep": darken(bg, 0.06),
            "surface": "#FFFFFF",
            "card": "#FFFFFF",
            "card_hover": mix("#FFFFFF", bg, 0.5),
            "border": mix(bg, "#1A1D29", 0.16),
            "text": "#1A1D29",
            "sub": mix(bg, "#1A1D29", 0.62),
            "accent": config.get("theme.accent", "#7C5CFF"),
            "success": "#18A05E",
            "danger": "#E23B5A",
            "warning": "#C77E12",
            "shadow": mix(bg, "#1A1D29", 0.25),
        }
    accent = t["accent"]
    button = config.get("theme.button_color", "") or accent
    t["button"] = button
    t["button_hover"] = lighten(button, 0.12) if luminance(button) < 120 else darken(button, 0.10)
    t["on_button"] = on_color(button)
    t["on_accent"] = on_color(accent)
    t["accent_soft"] = mix(accent, t["card"], 0.82) if dark else mix(accent, "#FFFFFF", 0.86)
    t["hover_soft"] = mix(t["card"], t["text"], 0.06)
    return t


def ctk_appearance() -> str:
    mode = config.get("theme.appearance", "dark")
    if mode == "system":
        return "system"
    return "dark" if mode == "dark" else "light"
