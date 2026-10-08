from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from IDE import supabase_config


REQUEST_TIMEOUT_SECONDS = 8
INSERT_TABLES = {
    "usage_surveys",
    "experience_surveys",
    "bug_reports",
    "feature_requests",
}
UPDATE_COLUMNS = "version,download_url,release_notes,mandatory,published_at"


class SupabaseError(Exception):
    """A user-safe Supabase configuration or request error."""


class SupabaseClient:
    def __init__(
        self,
        url: str | None = None,
        anon_key: str | None = None,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ):
        self.url = (
            url or os.environ.get("HANGULLO_SUPABASE_URL") or supabase_config.SUPABASE_URL
        ).strip().rstrip("/")
        self.anon_key = (
            anon_key
            or os.environ.get("HANGULLO_SUPABASE_ANON_KEY")
            or supabase_config.SUPABASE_ANON_KEY
        ).strip()
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        try:
            parsed = urlparse(self.url)
            parsed.port
        except ValueError:
            return False
        return bool(
            parsed.scheme == "https"
            and parsed.netloc
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and self.anon_key
        )

    def insert_usage_survey(self, payload: dict) -> None:
        self._insert("usage_surveys", payload)

    def insert_experience_survey(self, payload: dict) -> None:
        self._insert("experience_surveys", payload)

    def insert_bug_report(self, payload: dict) -> None:
        self._insert("bug_reports", payload)

    def insert_feature_request(self, payload: dict) -> None:
        self._insert("feature_requests", payload)

    def get_latest_update(self) -> dict | None:
        query = urlencode(
            {
                "select": UPDATE_COLUMNS,
                "order": "published_at.desc",
                "limit": "1",
            }
        )
        rows = self._request("app_updates", method="GET", query=query)
        if not isinstance(rows, list):
            raise SupabaseError("업데이트 정보를 읽을 수 없습니다.")
        if not rows:
            return None
        if not isinstance(rows[0], dict):
            raise SupabaseError("업데이트 정보 형식이 올바르지 않습니다.")
        return rows[0]

    def _insert(self, table: str, payload: dict) -> None:
        if table not in INSERT_TABLES:
            raise SupabaseError("허용되지 않은 데이터 테이블입니다.")
        self._request(table, method="POST", payload=payload)

    def _request(
        self,
        table: str,
        method: str,
        payload: dict | None = None,
        query: str = "",
    ):
        if not self.configured:
            raise SupabaseError("Supabase 연결 정보가 설정되지 않았습니다.")

        body = None
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            try:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError) as error:
                raise SupabaseError("전송할 데이터 형식이 올바르지 않습니다.") from error
            headers["Content-Type"] = "application/json"
            headers["Prefer"] = "return=minimal"

        request = Request(
            f"{self.url}/rest/v1/{table}{'?' + query if query else ''}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_body = response.read()
        except HTTPError as error:
            raise SupabaseError(
                f"Supabase 요청이 거부되었습니다 (HTTP {error.code})."
            ) from error
        except (URLError, OSError, TimeoutError) as error:
            raise SupabaseError("네트워크에 연결할 수 없습니다.") from error

        if not response_body:
            return None
        try:
            return json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SupabaseError("Supabase 응답을 읽을 수 없습니다.") from error


def get_client() -> SupabaseClient:
    return SupabaseClient()