import unittest

from IDE.update_checker import check_for_update, is_newer_version


class UpdateCheckerTests(unittest.TestCase):
    def test_compares_releases_and_prereleases(self):
        self.assertTrue(is_newer_version("0.0.2-beta", "0.0.1-beta"))
        self.assertTrue(is_newer_version("0.0.2", "0.0.2-beta"))
        self.assertFalse(is_newer_version("0.0.1-beta", "0.0.1"))
        self.assertFalse(is_newer_version("0.0.1", "0.0.1"))

    def test_accepts_general_http_and_https_links(self):
        class Client:
            def get_latest_update(self):
                return {
                    "version": "0.0.2-beta",
                    "download_url": "https://naver.com",
                }

        update = check_for_update(Client(), current_version="0.0.1-beta")
        self.assertIsNotNone(update)
        self.assertTrue(update.download_url_valid)

    def test_rejects_non_web_links(self):
        class Client:
            def get_latest_update(self):
                return {
                    "version": "0.0.2-beta",
                    "download_url": "file:///C:/installer.exe",
                }

        update = check_for_update(Client(), current_version="0.0.1-beta")
        self.assertFalse(update.download_url_valid)

    def test_returns_newer_github_release(self):
        class Client:
            def get_latest_update(self):
                return {
                    "version": "0.0.2-beta",
                    "download_url": "https://github.com/codexora-dev/Hangullo/releases/download/v0.0.2/Hangullo-Setup.exe",
                    "release_notes": "오류 수정",
                    "mandatory": False,
                }

        update = check_for_update(Client(), current_version="0.0.1-beta")
        self.assertEqual(update.version, "0.0.2-beta")
        self.assertEqual(update.release_notes, "오류 수정")
        self.assertTrue(update.download_url_valid)


if __name__ == "__main__":
    unittest.main()