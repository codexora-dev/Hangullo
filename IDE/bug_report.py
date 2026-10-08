from __future__ import annotations

import platform
import tkinter as tk
from tkinter import ttk

from IDE.feedback_ui import FeedbackDialog, client_metadata
from IDE.supabase_client import get_client


class BugReportDialog(FeedbackDialog):
    def __init__(self, app):
        super().__init__(app, "오류 보고", height=720)
        self.add_heading(
            "오류 보고",
            "프로젝트 코드와 개인 파일은 전송하지 않습니다. 오류 재현에 필요한 내용만 작성해 주세요.",
        )
        self.error_type = getattr(app, "last_error_type", "사용자 직접 보고")
        self.add_info("Hangullo 버전", client_metadata()["hangullo_version"])
        self.add_info("운영체제", platform.system())
        self.add_info("Python 버전", platform.python_version())
        self.add_info("오류 유형", self.error_type)
        self.add_entry("title", "오류 제목", required=True, limit=200)
        self.add_text("description", "오류 설명", required=True, height=5, limit=4000)
        self.add_text("reproduction_steps", "재현 방법", height=4, limit=3000)
        self.add_text("expected_result", "기대했던 결과", height=3, limit=2000)
        self.add_text("actual_result", "실제 결과", height=3, limit=2000)
        self.add_text("error_log", "선택한 오류 로그", height=4, limit=10000)
        self.include_log = tk.BooleanVar(value=False)
        log_widget = self.fields["error_log"][1]
        log_widget.configure(state="disabled")
        ttk.Checkbutton(
            self.form,
            text="직접 입력한 오류 로그를 함께 전송합니다",
            variable=self.include_log,
            command=lambda: log_widget.configure(
                state="normal" if self.include_log.get() else "disabled"
            ),
        ).pack(anchor="w", pady=(2, 10))

    def submit(self) -> None:
        values = self.collect(("title", "description"))
        if values is None:
            return
        if not self.include_log.get():
            values["error_log"] = ""
        payload = {
            **client_metadata(),
            "python_version": platform.python_version(),
            "error_type": self.error_type,
            **values,
        }
        client = get_client()
        self.submit_async(lambda: client.insert_bug_report(payload), lambda: None)