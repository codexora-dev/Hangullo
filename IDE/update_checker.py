from __future__ import annotations

import re
import webbrowser
from dataclasses import dataclass
from urllib.parse import urlparse

from IDE.supabase_client import SupabaseError, get_client
from IDE.window_utils import set_hangullo_icon
from version import __version__


VERSION_PATTERN = re.compile(r"^v?(\d+(?:\.\d+)*)(?:-([0-9A-Za-z][0-9A-Za-z.-]*))?$")


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str
    mandatory: bool
    download_url_valid: bool


def _version_key(value: str) -> tuple:
    match = VERSION_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError("지원하지 않는 버전 형식입니다.")
    numbers = tuple(int(part) for part in match.group(1).split("."))
    prerelease = match.group(2)
    if prerelease is None:
        return numbers, 1, ()
    tokens = []
    for part in re.split(r"[.-]", prerelease):
        tokens.append((0, int(part)) if part.isdigit() else (1, part.casefold()))
    return numbers, 0, tuple(tokens)


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_key = _version_key(candidate)
    current_key = _version_key(current)
    width = max(len(candidate_key[0]), len(current_key[0]))
    candidate_numbers = candidate_key[0] + (0,) * (width - len(candidate_key[0]))
    current_numbers = current_key[0] + (0,) * (width - len(current_key[0]))
    return (candidate_numbers, *candidate_key[1:]) > (current_numbers, *current_key[1:])


def check_for_update(client=None, current_version: str = __version__) -> UpdateInfo | None:
    update = (client or get_client()).get_latest_update()
    if update is None:
        return None

    version = update.get("version")
    if not isinstance(version, str) or not is_newer_version(version, current_version):
        return None
    download_url = update.get("download_url")
    parsed_url = urlparse(download_url if isinstance(download_url, str) else "")
    try:
        parsed_url.port
        download_url_valid = (
            parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.hostname)
            and not parsed_url.username
            and not parsed_url.password
        )
    except ValueError:
        download_url_valid = False
    release_notes = update.get("release_notes", "")
    if not isinstance(release_notes, str):
        release_notes = ""
    mandatory = update.get("mandatory", False)
    if not isinstance(mandatory, bool):
        mandatory = False
    return UpdateInfo(
        version, download_url, release_notes, mandatory, download_url_valid
    )


def show_update_dialog(app, update: UpdateInfo) -> None:
    import tkinter as tk
    from tkinter import BOTH, RIGHT, X, ttk

    window = tk.Toplevel(app.root)
    set_hangullo_icon(window)
    window.title("Hangullo 업데이트")
    window.geometry("520x420")
    window.minsize(440, 340)
    window.transient(app.root)

    frame = ttk.Frame(window, padding=20)
    frame.pack(fill=BOTH, expand=True)
    title = "새로운 Hangullo 버전이 있습니다."
    if update.mandatory:
        title += " (필수 업데이트)"
    ttk.Label(
        frame, text=title, font=(app.settings.font_family, 13, "bold")
    ).pack(anchor="w", pady=(0, 12))
    ttk.Label(frame, text=f"현재 버전: v{__version__}").pack(anchor="w", pady=2)
    ttk.Label(frame, text=f"최신 버전: v{update.version}").pack(anchor="w", pady=2)
    ttk.Label(frame, text="업데이트 내용").pack(anchor="w", pady=(14, 4))
    notes = tk.Text(
        frame,
        height=8,
        wrap="word",
        state="normal",
        font=(app.settings.font_family, 10),
        bg=app.palette["editor"],
        fg=app.palette["fg"],
        relief="solid",
        borderwidth=1,
    )
    notes.pack(fill=BOTH, expand=True)
    notes.insert("1.0", update.release_notes or "업데이트 내용이 등록되지 않았습니다.")
    notes.configure(state="disabled")
    if not update.download_url_valid:
        ttk.Label(
            frame,
            text="다운로드 주소가 올바르지 않아 개발자 확인이 필요합니다.",
            foreground=app.palette["error"],
            wraplength=480,
        ).pack(anchor="w", pady=(10, 0))

    buttons = ttk.Frame(frame)
    buttons.pack(fill=X, pady=(16, 0))
    update_button = ttk.Button(
        buttons, text="업데이트", command=lambda: _open_release(window, update)
    )
    update_button.pack(side=RIGHT)
    if not update.download_url_valid:
        update_button.configure(state="disabled")
    ttk.Button(buttons, text="나중에", command=window.destroy).pack(
        side=RIGHT, padx=(0, 8)
    )


def _open_release(window, update: UpdateInfo) -> None:
    try:
        opened = webbrowser.open(update.download_url)
    except Exception:
        opened = False
    if opened:
        window.destroy()
    else:
        from tkinter import messagebox

        messagebox.showerror(
            "업데이트 링크 열기 실패",
            "기본 브라우저에서 업데이트 주소를 열지 못했습니다.",
            parent=window,
        )