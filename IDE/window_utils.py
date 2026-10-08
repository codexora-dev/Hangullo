from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path


def set_hangullo_icon(window) -> None:
    project_root = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    )
    icon_path = project_root / "assets" / "icon" / "Hangullo_Logo2.ico"
    if not icon_path.is_file():
        return
    try:
        window.iconbitmap(str(icon_path))
    except (OSError, tk.TclError):
        pass