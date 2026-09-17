#!/usr/bin/env python3
"""Launcher do Custom MF (usado pelo PyInstaller)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if "--selftest" in sys.argv[1:] and "--no-ui" in sys.argv[1:]:
    # modo de teste leve: não precisa de tkinter/customtkinter
    from app.selftest import run_selftest
    sys.exit(run_selftest(ui=False))

from app.main import run  # noqa: E402

if __name__ == "__main__":
    run()
