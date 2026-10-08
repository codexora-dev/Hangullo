import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from IDE.app import DEFAULT_HANGULLO_ROOT, HangulloIDE, resolve_workspace_path


class WorkspaceResolutionTests(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        root.mkdir(parents=True)
        (root / "main.py").touch()
        for name in ("compiler", "lexer", "parser"):
            (root / name).mkdir()
        return root

    def test_first_run_finds_project_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.make_project(root / "Hangullo")

            result = resolve_workspace_path(root / "missing", True, [project])

            self.assertEqual(result, project)

    def test_missing_saved_path_recovers_project_even_after_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.make_project(root / "Hangullo")

            result = resolve_workspace_path(root / "old-computer-path", False, [project])

            self.assertEqual(result, project)

    def test_existing_workspace_is_preserved_after_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()

            result = resolve_workspace_path(workspace, False, [])

            self.assertEqual(result, workspace)

    def test_missing_workspace_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"

            result = resolve_workspace_path(missing, False, [])

            self.assertEqual(result, DEFAULT_HANGULLO_ROOT)


class UsageSurveyMenuTests(unittest.TestCase):
    def test_completed_survey_does_not_open_dialog(self):
        app = object.__new__(HangulloIDE)
        app.settings = SimpleNamespace(usage_survey_completed=True)

        with patch("IDE.app.UsageSurveyDialog") as survey_dialog:
            app.open_usage_survey()

        survey_dialog.assert_not_called()

    def test_incomplete_survey_can_open_dialog(self):
        app = object.__new__(HangulloIDE)
        app.settings = SimpleNamespace(usage_survey_completed=False)

        with patch("IDE.app.UsageSurveyDialog") as survey_dialog:
            app.open_usage_survey()

        survey_dialog.assert_called_once_with(app)


if __name__ == "__main__":
    unittest.main()