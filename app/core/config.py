"""Configuração persistente do app (JSON) com valores padrão."""
from __future__ import annotations

import copy
import json
import threading

from . import paths

_lock = threading.RLock()

DEFAULTS: dict = {
    "first_run_done": False,
    "theme": {
        "appearance": "dark",      # dark | light | system
        "bg_tone": "padrao",       # dark: profundo|padrao|suave — light: branco|padrao|gelo
        "accent": "#7C5CFF",       # cor de destaque
        "button_color": "",        # "" = seguir a cor de destaque
        "icon_pack": "Neon Padrão",
    },
    "cursor": {
        "active": "",              # nome do pacote aplicado
        "custom_image": "",        # caminho da imagem usada como cursor
    },
    "fx": {
        "click_enabled": False,
        "click_type": "onda",      # onda|pulso|faiscas|estrelas|coracoes|flash|fogos
        "click_color": "#7C5CFF",
        "click_rainbow": False,
        "click_size": 1.0,         # 0.5 .. 2.5
        "click_duration": 1.0,     # 0.5 .. 2.0
        "trail_enabled": False,
        "trail_type": "neon",      # neon|arcoiris|bolhas|estrelas|coracoes|fogo|po
        "trail_color": "#3DDC97",
        "trail_rainbow": False,
        "trail_size": 1.0,         # 0.5 .. 2.5
        "trail_density": 3,        # 1 .. 5
        "trail_duration": 1.0,     # 0.5 .. 2.0
    },
    "font": {
        "applied": "",             # fonte substituta aplicada ao Windows ("" = nenhuma)
    },
}

_data: dict = copy.deepcopy(DEFAULTS)


def load() -> dict:
    global _data
    with _lock:
        try:
            raw = json.loads(paths.config_file().read_text("utf-8"))
            if isinstance(raw, dict):
                _data = _merge(copy.deepcopy(DEFAULTS), raw)
        except Exception:
            _data = copy.deepcopy(DEFAULTS)
        return _data


def _merge(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def save() -> None:
    with _lock:
        try:
            paths.config_file().write_text(
                json.dumps(_data, indent=2, ensure_ascii=False), "utf-8")
        except Exception:
            pass


def get(path: str, default=None):
    """get("fx.click_type")"""
    with _lock:
        node: object = _data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def set(path: str, value, do_save: bool = True) -> None:
    with _lock:
        parts = path.split(".")
        node = _data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        if do_save:
            save()


def reset_theme() -> None:
    with _lock:
        _data["theme"] = copy.deepcopy(DEFAULTS["theme"])
        save()
