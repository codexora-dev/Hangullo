from __future__ import annotations

import platform
import queue
import threading
import tkinter as tk
from tkinter import BOTH, BOTTOM, LEFT, RIGHT, X, Y, ttk

from IDE.window_utils import set_hangullo_icon
from version import __version__


def client_metadata() -> dict[str, str]:
    return {"hangullo_version": __version__, "os": platform.system()}


class FeedbackDialog(tk.Toplevel):
    def __init__(self, app, title: str, height: int = 650):
        super().__init__(app.root)
        set_hangullo_icon(self)
        self.app = app
        self.title(title)
        self.geometry(f"600x{height}")
        self.minsize(500, 450)
        self.transient(app.root)
        self.fields: dict[str, tuple[str, object]] = {}
        self.busy = False
        self._request_queue: queue.Queue[tuple[bool, str | None]] = queue.Queue()

        area = ttk.Frame(self)
        area.pack(fill=BOTH, expand=True)
        self.canvas = tk.Canvas(
            area,
            highlightthickness=0,
            background=app.palette["window"],
        )
        scrollbar = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.form = ttk.Frame(self.canvas, padding=20)
        self.form_window = self.canvas.create_window(
            (0, 0), window=self.form, anchor="nw"
        )
        self.form.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_form)

        footer = ttk.Frame(self, padding=(18, 10))
        footer.pack(side=BOTTOM, fill=X)
        self.status = ttk.Label(footer, text="", wraplength=390)
        self.status.pack(side=LEFT, fill=X, expand=True)
        self.cancel_button = ttk.Button(
            footer, text="닫기", command=self.destroy
        )
        self.cancel_button.pack(side=RIGHT, padx=(8, 0))
        self.submit_button = ttk.Button(
            footer, text="제출", command=self.submit
        )
        self.submit_button.pack(side=RIGHT)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _update_scroll_region(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_form(self, event) -> None:
        self.canvas.itemconfigure(self.form_window, width=event.width)

    def add_heading(self, text: str, description: str = "") -> None:
        ttk.Label(
            self.form, text=text, font=(self.app.settings.font_family, 14, "bold")
        ).pack(anchor="w", pady=(0, 4))
        if description:
            ttk.Label(
                self.form, text=description, wraplength=520, justify="left"
            ).pack(anchor="w", pady=(0, 14))

    def add_choice(self, key: str, label: str, choices: tuple[str, ...]) -> None:
        group = ttk.Frame(self.form)
        group.pack(fill=X, pady=6)
        ttk.Label(group, text=label).pack(anchor="w", pady=(0, 4))
        variable = tk.StringVar(value="")
        ttk.Combobox(
            group,
            textvariable=variable,
            values=choices,
            state="readonly",
        ).pack(fill=X)
        self.fields[key] = ("choice", variable)

    def add_rating(self, key: str, label: str) -> None:
        self.add_choice(key, label, ("1", "2", "3", "4", "5"))

    def add_entry(
        self, key: str, label: str, required: bool = False, limit: int = 200
    ) -> None:
        group = ttk.Frame(self.form)
        group.pack(fill=X, pady=6)
        suffix = " *" if required else ""
        ttk.Label(group, text=label + suffix).pack(anchor="w", pady=(0, 4))
        entry = ttk.Entry(group)
        entry.pack(fill=X)
        self.fields[key] = ("entry", entry)
        entry.limit = limit

    def add_text(
        self,
        key: str,
        label: str,
        required: bool = False,
        height: int = 4,
        limit: int = 4000,
    ) -> None:
        group = ttk.Frame(self.form)
        group.pack(fill=X, pady=6)
        suffix = " *" if required else ""
        ttk.Label(group, text=label + suffix).pack(anchor="w", pady=(0, 4))
        text = tk.Text(
            group,
            height=height,
            wrap="word",
            font=(self.app.settings.font_family, 10),
            bg=self.app.palette["editor"],
            fg=self.app.palette["fg"],
            insertbackground=self.app.palette["fg"],
            relief="solid",
            borderwidth=1,
        )
        text.pack(fill=X)
        self.fields[key] = ("text", text)
        text.limit = limit

    def add_multiselect(
        self, key: str, label: str, choices: tuple[str, ...]
    ) -> None:
        group = ttk.LabelFrame(self.form, text=label, padding=10)
        group.pack(fill=X, pady=8)
        variables = []
        for choice in choices:
            variable = tk.BooleanVar(value=False)
            ttk.Checkbutton(group, text=choice, variable=variable).pack(
                anchor="w", pady=2
            )
            variables.append((choice, variable))
        self.fields[key] = ("multiselect", variables)

    def add_info(self, label: str, value: str) -> None:
        ttk.Label(
            self.form, text=f"{label}: {value}", wraplength=520
        ).pack(anchor="w", pady=3)

    def collect(self, required: tuple[str, ...] = ()) -> dict:
        values = {}
        for key, (kind, field) in self.fields.items():
            if kind == "choice":
                value = field.get().strip()
            elif kind == "entry":
                value = field.get().strip()
            elif kind == "text":
                value = field.get("1.0", "end-1c").strip()
            else:
                value = [label for label, variable in field if variable.get()]

            if key in required and not value:
                self.show_status("필수 항목을 입력하거나 선택해 주세요.", error=True)
                return None
            if hasattr(field, "limit") and len(value) > field.limit:
                self.show_status("입력 내용이 허용된 길이를 초과했습니다.", error=True)
                return None
            values[key] = value
        return values

    def submit_async(self, action, on_success) -> None:
        if self.busy:
            return
        self.busy = True
        self.submit_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        self.show_status("전송 중입니다...")

        def send() -> None:
            try:
                action()
                self._request_queue.put((True, None))
            except Exception as error:
                self._request_queue.put((False, str(error)))

        threading.Thread(target=send, daemon=True).start()
        self.after(100, lambda: self._poll_request(on_success))

    def _poll_request(self, on_success) -> None:
        try:
            succeeded, error = self._request_queue.get_nowait()
        except queue.Empty:
            self.after(100, lambda: self._poll_request(on_success))
            return

        self.busy = False
        self.submit_button.configure(state="normal")
        self.cancel_button.configure(state="normal")
        if succeeded:
            success_message = on_success()
            self.show_status(
                success_message or "제출했습니다. 참여해 주셔서 감사합니다."
            )
            self.after(1000, self.destroy)
        else:
            self.show_status(error or "전송하지 못했습니다. 다시 시도해 주세요.", error=True)

    def show_status(self, text: str, error: bool = False) -> None:
        self.status.configure(
            text=text,
            foreground=self.app.palette["error"] if error else self.app.palette["muted"],
        )

    def _close(self) -> None:
        if not self.busy:
            self.destroy()

    def submit(self) -> None:
        raise NotImplementedError