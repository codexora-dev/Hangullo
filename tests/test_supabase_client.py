import io
import json
import os
import unittest
from unittest.mock import patch

from IDE import supabase_config
from IDE.supabase_client import SupabaseClient, SupabaseError


class SupabaseClientTests(unittest.TestCase):
    def setUp(self):
        self.client = SupabaseClient(
            url="https://example.supabase.co", anon_key="public-anon-key", timeout=3
        )

    @patch("IDE.supabase_client.urlopen")
    def test_insert_sends_only_the_requested_payload(self, urlopen):
        urlopen.return_value = io.BytesIO(b"")
        payload = {"usage_type": "개인 프로젝트"}

        self.client.insert_usage_survey(payload)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertTrue(request.full_url.endswith("/rest/v1/usage_surveys"))
        self.assertEqual(json.loads(request.data), payload)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 3)
        self.assertEqual(request.get_header("Prefer"), "return=minimal")

    @patch("IDE.supabase_client.urlopen")
    def test_update_query_reads_only_public_update_fields(self, urlopen):
        update = {
            "version": "0.0.2-beta",
            "download_url": "https://github.com/codexora-dev/Hangullo/releases/download/v0.0.2/Hangullo.exe",
            "release_notes": "개선",
            "mandatory": False,
            "published_at": "2026-10-08T00:00:00Z",
        }
        urlopen.return_value = io.BytesIO(json.dumps([update]).encode("utf-8"))

        self.assertEqual(self.client.get_latest_update(), update)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "GET")
        self.assertIn("/rest/v1/app_updates?", request.full_url)
        self.assertIn("select=version%2Cdownload_url", request.full_url)

    def test_missing_or_insecure_configuration_is_rejected(self):
        with patch.dict(
            os.environ,
            {"HANGULLO_SUPABASE_URL": "", "HANGULLO_SUPABASE_ANON_KEY": ""},
        ):
            with patch.object(supabase_config, "SUPABASE_URL", ""), patch.object(
                supabase_config, "SUPABASE_ANON_KEY", ""
            ):
                with self.assertRaisesRegex(SupabaseError, "설정되지 않았습니다"):
                    SupabaseClient().get_latest_update()
        with self.assertRaisesRegex(SupabaseError, "설정되지 않았습니다"):
            SupabaseClient(url="http://example.supabase.co", anon_key="key").get_latest_update()

    def test_unknown_insert_table_is_rejected(self):
        with self.assertRaisesRegex(SupabaseError, "허용되지 않은"):
            self.client._insert("app_updates", {})


if __name__ == "__main__":
    unittest.main()