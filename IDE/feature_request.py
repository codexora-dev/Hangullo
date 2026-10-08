from __future__ import annotations

from IDE.feedback_ui import FeedbackDialog, client_metadata
from IDE.supabase_client import get_client


class FeatureRequestDialog(FeedbackDialog):
    def __init__(self, app):
        super().__init__(app, "기능 요청", height=650)
        self.add_heading(
            "기능 요청",
            "원하는 기능과 사용 목적을 알려주세요. 이름이나 연락처는 수집하지 않습니다.",
        )
        self.add_entry("title", "기능 이름", required=True, limit=200)
        self.add_text("description", "기능 설명", required=True, height=5, limit=4000)
        self.add_text("reason", "필요한 이유", height=4, limit=3000)
        self.add_text("example", "사용 예시", height=4, limit=3000)

    def submit(self) -> None:
        values = self.collect(("title", "description"))
        if values is None:
            return
        payload = {**client_metadata(), **values}
        client = get_client()
        self.submit_async(lambda: client.insert_feature_request(payload), lambda: None)