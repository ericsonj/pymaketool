import unittest
import warnings
from pathlib import Path
import tempfile

from pymakelib import prelib
from pymakelib import preconts as K
from pymakelib import make_files


class TestResolveConfigDir(unittest.TestCase):

    def _make_tmp(self):
        """Create a fresh temporary directory and return its Path."""
        tmp = tempfile.mkdtemp()
        return Path(tmp)

    def test_legacy_layout_returns_root(self):
        root = self._make_tmp()
        (root / K.MAKEFILE_PY).touch()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            config_dir, mode = prelib.resolve_config_dir(root)
        self.assertEqual(mode, 'legacy')
        self.assertEqual(config_dir, root)

    def test_subdir_layout_returns_subdir(self):
        root = self._make_tmp()
        subdir = root / 'pymake'
        subdir.mkdir()
        (subdir / K.MAKEFILE_PY).touch()
        config_dir, mode = prelib.resolve_config_dir(root)
        self.assertEqual(mode, 'subdir')
        self.assertEqual(config_dir, subdir)

    def test_subdir_wins_over_root_when_both_exist(self):
        root = self._make_tmp()
        (root / K.MAKEFILE_PY).touch()  # legacy also present
        subdir = root / 'pymake'
        subdir.mkdir()
        (subdir / K.MAKEFILE_PY).touch()
        config_dir, mode = prelib.resolve_config_dir(root)
        self.assertEqual(mode, 'subdir')
        self.assertEqual(config_dir, subdir)

    def test_other_candidates_are_detected(self):
        for candidate in K.MAKEFILE_SUBDIR_CANDIDATES:
            with self.subTest(candidate=candidate):
                root = self._make_tmp()
                subdir = root / candidate
                subdir.mkdir()
                (subdir / K.MAKEFILE_PY).touch()
                config_dir, mode = prelib.resolve_config_dir(root)
                self.assertEqual(mode, 'subdir')
                self.assertEqual(config_dir.name, candidate)

    def test_error_when_no_makefile_py_found(self):
        root = self._make_tmp()
        with self.assertRaises(FileNotFoundError):
            prelib.resolve_config_dir(root)

    def test_legacy_layout_emits_deprecation_warning(self):
        root = self._make_tmp()
        (root / K.MAKEFILE_PY).touch()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            prelib.resolve_config_dir(root)
        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertTrue(
            len(deprecation_warnings) > 0,
            "Expected a DeprecationWarning for legacy layout, got none"
        )
        self.assertIn('deprecated', str(deprecation_warnings[0].message).lower())

    def test_subdir_layout_does_not_emit_deprecation_warning(self):
        root = self._make_tmp()
        subdir = root / 'pymake'
        subdir.mkdir()
        (subdir / K.MAKEFILE_PY).touch()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            prelib.resolve_config_dir(root)
        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(len(deprecation_warnings), 0)


class TestMakefileTemplates(unittest.TestCase):

    def test_legacy_makefile_references_makefile_mk_at_root(self):
        content = make_files.get_makefile_content(subdir=None)
        self.assertIn('-f makefile.mk', content)
        self.assertNotIn('pymake/', content)

    def test_subdir_makefile_references_makefile_mk_in_subdir(self):
        content = make_files.get_makefile_content(subdir='pymake')
        self.assertIn('-f pymake/makefile.mk', content)

    def test_legacy_makefile_mk_includes_at_root(self):
        content = make_files.get_makefile_mk_content(subdir=None)
        self.assertIn('include vars.mk', content)
        self.assertIn('include srcs.mk', content)
        self.assertIn('include targets.mk', content)
        self.assertNotIn('pymake/', content)

    def test_subdir_makefile_mk_includes_with_prefix(self):
        content = make_files.get_makefile_mk_content(subdir='pymake')
        self.assertIn('include pymake/vars.mk', content)
        self.assertIn('include pymake/srcs.mk', content)
        self.assertIn('include pymake/targets.mk', content)

    def test_preferred_subdir_is_pymake(self):
        self.assertEqual(K.MAKEFILE_SUBDIR_CANDIDATES[0], 'pymake')


if __name__ == '__main__':
    unittest.main()
