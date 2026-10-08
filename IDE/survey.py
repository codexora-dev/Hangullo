from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from IDE.feedback_ui import FeedbackDialog, client_metadata
from IDE.supabase_client import get_client
from IDE.window_utils import set_hangullo_icon


USAGE_TYPES = (
    "코딩 입문/공부",
    "학교 수업",
    "개인 프로젝트",
    "대회/해커톤",
    "취미",
    "다른 프로그래밍 언어를 배우기 위한 준비",
    "기타",
)
EXPERIENCE_LEVELS = ("처음 시작함", "1개월 미만", "1~6개월", "6개월~1년", "1년 이상")
DISCOVERY_SOURCES = (
    "친구/지인",
    "학교/선생님",
    "블로그",
    "GitHub",
    "검색",
    "커뮤니티/SNS",
    "기타",
)
USAGE_FREQUENCIES = (
    "거의 매일",
    "일주일에 여러 번",
    "일주일에 한 번 정도",
    "가끔",
    "아직 모르겠음",
)
DESIRED_FEATURES = (
    "자동완성",
    "코드 하이라이팅 개선",
    "디버거",
    "자세한 오류 메시지",
    "실행 결과 개선",
    "블록 코딩 개선",
    "패키지/라이브러리 시스템",
    "문서/튜토리얼",
    "예제 프로그램",
    "기타",
)


class UsageSurveyDialog(FeedbackDialog):
    def __init__(self, app):
        super().__init__(app, "사용 수요 조사", height=620)
        self.add_heading(
            "Hangullo 사용 수요 조사",
            "개인정보를 입력하지 않아도 됩니다. 응답은 사용 현황을 파악하는 데만 사용됩니다.",
        )
        self.add_choice("usage_type", "사용 목적", USAGE_TYPES)
        self.add_choice("experience_level", "프로그래밍 경험", EXPERIENCE_LEVELS)
        self.add_choice("discovery_source", "Hangullo를 알게 된 경로", DISCOVERY_SOURCES)
        self.add_choice("usage_frequency", "사용 빈도", USAGE_FREQUENCIES)

    def submit(self) -> None:
        values = self.collect(
            ("usage_type", "experience_level", "discovery_source", "usage_frequency")
        )
        if values is None:
            return
        payload = {**client_metadata(), **values}
        client = get_client()
        self.submit_async(
            lambda: client.insert_usage_survey(payload), self._mark_completed
        )

    def _mark_completed(self) -> str | None:
        self.app.settings.usage_survey_completed = True
        self.app.remove_usage_survey_menu_item()
        try:
            self.app.settings.save()
        except OSError:
            return "응답은 제출했지만 완료 상태를 저장하지 못했습니다."
        return None


class ExperienceSurveyDialog(FeedbackDialog):
    def __init__(self, app):
        super().__init__(app, "사용 경험 조사", height=700)
        self.add_heading(
            "Hangullo 사용 경험 조사",
            "응답은 IDE와 학습 경험을 개선하는 데 사용됩니다. 이름이나 연락처는 수집하지 않습니다.",
        )
        self.add_rating("grammar_ease", "문법 이해도")
        self.add_rating("ide_ease", "IDE 사용 편의성")
        self.add_rating("recommendation_score", "다른 사람에게 추천할 의향")
        self.add_text("best_point", "가장 좋았던 점", height=3)
        self.add_text("worst_point", "가장 불편했던 점", height=3)
        self.add_multiselect("desired_features", "추가되었으면 하는 기능", DESIRED_FEATURES)
        self.add_rating("satisfaction", "만족도")
        self.add_text("feedback", "기타 의견", height=3)

    def submit(self) -> None:
        values = self.collect(
            ("grammar_ease", "ide_ease", "recommendation_score", "satisfaction")
        )
        if values is None:
            return
        for field in ("grammar_ease", "ide_ease", "recommendation_score", "satisfaction"):
            values[field] = int(values[field])
        payload = {**client_metadata(), **values}
        client = get_client()
        self.submit_async(lambda: client.insert_experience_survey(payload), lambda: None)


class UsageSurveyPrompt(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        set_hangullo_icon(self)
        self.app = app
        self.title("Hangullo 사용 수요 조사")
        self.resizable(False, False)
        self.transient(app.root)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        frame = ttk.Frame(self, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="Hangullo 사용 수요 조사",
            font=(app.settings.font_family, 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            frame,
            text="Hangullo를 어떤 목적으로 사용하시나요?\n응답은 선택 사항이며 나중에 도움말 메뉴에서 참여할 수 있습니다.",
            justify="left",
        ).pack(anchor="w", pady=(0, 18))
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="e")
        ttk.Button(buttons, text="나중에 하기", command=self.destroy).pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(buttons, text="설문 시작", command=self._start).pack(side="right")

    def _start(self) -> None:
        self.destroy()
        UsageSurveyDialog(self.app)