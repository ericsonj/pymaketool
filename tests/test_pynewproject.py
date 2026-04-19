"""Tests for the refactored pynewproject (copier-based)."""

import json
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------

FAKE_CATALOG = {
    "version": 1,
    "repo": "https://github.com/ericsonj/pymaketool-templates.git",
    "templates": [
        {
            "name": "clinuxgcc",
            "display_name": "C Linux GCC",
            "description": "Basic C project for Linux with GCC toolchain",
            "subdirectory": "templates/clinuxgcc",
            "tags": ["linux", "gcc", "c"],
            "category": "linux",
            "version": "1.0.0",
            "min_pymaketool": "3.0.0",
        },
        {
            "name": "cortex_m_gcc",
            "display_name": "ARM Cortex-M GCC",
            "description": "Bare-metal ARM Cortex-M with arm-none-eabi-gcc",
            "subdirectory": "templates/cortex_m_gcc",
            "tags": ["arm", "cortex-m", "embedded"],
            "category": "embedded",
            "version": "1.0.0",
            "min_pymaketool": "3.0.0",
        },
    ],
}


class TestFetchCatalog(unittest.TestCase):

    def _make_response(self, data: dict):
        raw = json.dumps(data).encode()
        resp = MagicMock()
        resp.read.return_value = raw
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    @patch("pynewproject.catalog.CACHE_FILE")
    @patch("pynewproject.catalog.urlopen")
    def test_fetch_from_network_when_no_cache(self, mock_urlopen, mock_cache_file):
        mock_cache_file.exists.return_value = False
        mock_cache_file.parent.mkdir = MagicMock()
        mock_cache_file.write_text = MagicMock()
        mock_urlopen.return_value = self._make_response(FAKE_CATALOG)

        from pynewproject.catalog import fetch_catalog

        result = fetch_catalog(refresh=True)
        self.assertEqual(result["version"], 1)
        self.assertEqual(len(result["templates"]), 2)

    @patch("pynewproject.catalog._PROCESS_CACHE", None)
    @patch("pynewproject.catalog.CACHE_FILE")
    @patch("pynewproject.catalog.time")
    def test_returns_cache_when_fresh(self, mock_time, mock_cache_file):
        mock_time.time.return_value = 1000
        mock_cache_file.exists.return_value = True
        mock_cache_file.stat.return_value.st_mtime = 999  # 1 second old
        mock_cache_file.read_text.return_value = json.dumps(FAKE_CATALOG)

        from pynewproject.catalog import fetch_catalog

        result = fetch_catalog()
        self.assertEqual(result["templates"][0]["name"], "clinuxgcc")
        mock_cache_file.read_text.assert_called_once()


class TestFindTemplate(unittest.TestCase):

    def test_found_exact(self):
        from pynewproject.catalog import find_template

        result = find_template(FAKE_CATALOG, "clinuxgcc")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "clinuxgcc")

    def test_found_case_insensitive(self):
        from pynewproject.catalog import find_template

        result = find_template(FAKE_CATALOG, "CLINUXGCC")
        self.assertIsNotNone(result)

    def test_not_found(self):
        from pynewproject.catalog import find_template

        result = find_template(FAKE_CATALOG, "does_not_exist")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

class TestCmdNew(unittest.TestCase):

    @patch("pynewproject.commands.fetch_catalog", return_value=FAKE_CATALOG)
    @patch("pynewproject.commands.run_copy")
    def test_calls_run_copy_with_correct_args(self, mock_run_copy, _mock_catalog):
        from pynewproject.commands import cmd_new

        args = SimpleNamespace(
            template="clinuxgcc",
            output="/tmp/out",
            ref="v1.0.0",
            defaults=False,
            data=["project_name=myapp", "author=Test User"],
        )
        cmd_new(args)

        mock_run_copy.assert_called_once()
        call_kwargs = mock_run_copy.call_args.kwargs
        self.assertEqual(
            call_kwargs["src_path"],
            "https://github.com/ericsonj/pymaketool-templates.git",
        )
        self.assertEqual(call_kwargs["subdirectory"], "templates/clinuxgcc")
        self.assertEqual(call_kwargs["vcs_ref"], "v1.0.0")
        self.assertEqual(call_kwargs["data"], {"project_name": "myapp", "author": "Test User"})

    @patch("pynewproject.commands.fetch_catalog", return_value=FAKE_CATALOG)
    def test_exits_when_template_not_found(self, _mock_catalog):
        from pynewproject.commands import cmd_new

        args = SimpleNamespace(
            template="nonexistent",
            output=".",
            ref=None,
            defaults=False,
            data=[],
        )
        with self.assertRaises(SystemExit):
            cmd_new(args)


class TestCmdUpdate(unittest.TestCase):

    @patch("pynewproject.commands.run_update")
    def test_calls_run_update(self, mock_run_update, tmp_path=None):
        import tempfile, os
        from pynewproject.commands import cmd_update

        with tempfile.TemporaryDirectory() as tmp:
            answers = os.path.join(tmp, ".copier-answers.yml")
            open(answers, "w").close()  # create the file

            args = SimpleNamespace(path=tmp, ref="v1.1.0", conflict="inline")
            cmd_update(args)

            mock_run_update.assert_called_once()
            call_kwargs = mock_run_update.call_args.kwargs
            self.assertEqual(call_kwargs["dst_path"], tmp)
            self.assertEqual(call_kwargs["vcs_ref"], "v1.1.0")

    def test_exits_without_answers_file(self):
        import tempfile
        from pynewproject.commands import cmd_update

        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(path=tmp, ref=None, conflict="inline")
            with self.assertRaises(SystemExit):
                cmd_update(args)


class TestCmdList(unittest.TestCase):

    @patch("pynewproject.commands.fetch_catalog", return_value=FAKE_CATALOG)
    def test_list_all(self, _mock_catalog):
        from pynewproject.commands import cmd_list
        import io, sys

        args = SimpleNamespace(category=None, tag=None, refresh=False, json=False)
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            cmd_list(args)
        output = captured.getvalue()
        self.assertIn("clinuxgcc", output)
        self.assertIn("cortex_m_gcc", output)

    @patch("pynewproject.commands.fetch_catalog", return_value=FAKE_CATALOG)
    def test_list_filter_category(self, _mock_catalog):
        from pynewproject.commands import cmd_list
        import io, sys

        args = SimpleNamespace(category="embedded", tag=None, refresh=False, json=False)
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            cmd_list(args)
        output = captured.getvalue()
        self.assertIn("cortex_m_gcc", output)
        self.assertNotIn("clinuxgcc", output)


# ---------------------------------------------------------------------------
# legacy shim
# ---------------------------------------------------------------------------

class TestLegacy(unittest.TestCase):

    def test_detects_old_style(self):
        from pynewproject.legacy import detect_legacy

        self.assertTrue(detect_legacy(["CLinuxGCC", "project_name=foo"], FAKE_CATALOG))

    def test_ignores_known_commands(self):
        from pynewproject.legacy import detect_legacy

        self.assertFalse(detect_legacy(["list"], FAKE_CATALOG))
        self.assertFalse(detect_legacy(["new", "clinuxgcc"], FAKE_CATALOG))

    def test_ignores_unknown_names(self):
        from pynewproject.legacy import detect_legacy

        self.assertFalse(detect_legacy(["UnknownGenerator"], FAKE_CATALOG))

    @patch("pynewproject.commands.fetch_catalog", return_value=FAKE_CATALOG)
    @patch("pynewproject.commands.run_copy")
    def test_run_legacy_warns_and_delegates(self, mock_run_copy, _mock_catalog):
        from pynewproject.legacy import run_legacy

        with self.assertWarns(DeprecationWarning):
            run_legacy(["CLinuxGCC", "project_name=legacy_test"], FAKE_CATALOG)

        mock_run_copy.assert_called_once()
        call_kwargs = mock_run_copy.call_args.kwargs
        self.assertEqual(call_kwargs["subdirectory"], "templates/clinuxgcc")


# ---------------------------------------------------------------------------
# nproject deprecation
# ---------------------------------------------------------------------------

class TestNprojectDeprecation(unittest.TestCase):

    def test_importing_nproject_warns(self):
        import importlib, sys

        # Remove cached module so the warning fires again
        sys.modules.pop("pymakelib.nproject", None)
        with self.assertWarns(DeprecationWarning):
            importlib.import_module("pymakelib.nproject")


if __name__ == "__main__":
    unittest.main()
