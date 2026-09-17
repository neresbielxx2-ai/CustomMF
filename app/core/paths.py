"""Resolução de caminhos: recursos empacotados e pasta de dados do usuário."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "CustomMF"


def app_data_dir() -> Path:
    """Pasta gravável (APPDATA no Windows) para config, packs baixados etc."""
    base = os.getenv("APPDATA") or str(Path.home() / ".custommf")
    d = Path(base) / APP_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def assets_dir() -> Path:
    """Recursos embutidos no executável (app/assets)."""
    return Path(__file__).resolve().parent.parent / "assets"


def asset(name: str) -> Path:
    return assets_dir() / name


def _sub(name: str) -> Path:
    d = app_data_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def packs_root() -> Path:
    """Onde ficam os pacotes de cursor baixados/importados."""
    return _sub("cursors")


def active_cursor_dir() -> Path:
    """Cópia dos arquivos do cursor ativo (o registro aponta para cá)."""
    return _sub("active_cursor")


def icon_packs_dir() -> Path:
    """Pacotes de ícones (UI) importados pelo usuário."""
    return _sub("icon_packs")


def backup_file() -> Path:
    return app_data_dir() / "cursor_backup.json"


def config_file() -> Path:
    return app_data_dir() / "config.json"


def fonts_dir() -> Path:
    """Fontes instaladas pelo usuário pelo app (cópias)."""
    return _sub("fonts")


def temp_dir() -> Path:
    return _sub("tmp")


def crash_log() -> Path:
    return app_data_dir() / "crash.log"
