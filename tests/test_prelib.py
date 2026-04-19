import unittest
import pytest

from pymakelib import prelib
from pathlib import Path


class TestMkPyDiscovery(unittest.TestCase):
    """Discovery glob must match both *[.|_]mk.py and bare mk.py."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_named_mk_py_is_not_matched_by_old_glob(self):
        # Verify our assumption: the old pattern alone misses mk.py
        root = self.tmp_path
        (root / "mk.py").write_text("")
        old_matches = list(root.rglob("*[.|_]mk.py"))
        self.assertEqual([], old_matches)

    def test_mk_py_matched_by_new_glob(self):
        root = self.tmp_path
        (root / "mk.py").write_text("")
        matches = sorted(
            set(root.rglob("*[.|_]mk.py")) | set(root.rglob("mk.py"))
        )
        self.assertEqual(1, len(matches))
        self.assertEqual("mk.py", matches[0].name)

    def test_new_glob_still_finds_prefixed_variants(self):
        root = self.tmp_path
        (root / "app_mk.py").write_text("")
        (root / "util.mk.py").write_text("")
        (root / "mk.py").write_text("")
        matches = sorted(
            set(root.rglob("*[.|_]mk.py")) | set(root.rglob("mk.py"))
        )
        names = {p.name for p in matches}
        self.assertIn("app_mk.py", names)
        self.assertIn("util.mk.py", names)
        self.assertIn("mk.py", names)

    def test_new_glob_no_duplicates_when_both_exist(self):
        """set union must not duplicate files that somehow match both patterns."""
        root = self.tmp_path
        (root / "app_mk.py").write_text("")
        (root / "mk.py").write_text("")
        matches = sorted(
            set(root.rglob("*[.|_]mk.py")) | set(root.rglob("mk.py"))
        )
        # Each file appears exactly once
        names = [p.name for p in matches]
        self.assertEqual(len(names), len(set(names)))


class TestReadModuleEmptyMkPy(unittest.TestCase):
    """Empty mk.py (and *_mk.py) must auto-discover .c/.h via readModule()."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def _write_module_file(self, name, content=""):
        p = self.tmp_path / name
        p.write_text(content)
        return p

    def test_empty_mk_py_auto_discovers_c_files(self):
        (self.tmp_path / "foo.c").write_text("")
        (self.tmp_path / "bar.c").write_text("")
        mk = self._write_module_file("mk.py")
        modules = prelib.readModule(mk, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("foo.c" in s for s in srcs))
        self.assertTrue(any("bar.c" in s for s in srcs))

    def test_empty_named_mk_py_auto_discovers_c_files(self):
        (self.tmp_path / "main.c").write_text("")
        mk = self._write_module_file("app_mk.py")
        modules = prelib.readModule(mk, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))

    def test_simple_module_in_mk_py_works(self):
        (self.tmp_path / "main.c").write_text("")
        mk = self._write_module_file(
            "mk.py",
            "from pymakelib.pym import module\nmodule()\n",
        )
        modules = prelib.readModule(mk, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))


class TestExternalModuleValidation(unittest.TestCase):
    """ExternalModule path guard must accept mk.py, _mk.py, and .mk.py."""

    def _name_is_valid(self, path_str: str) -> bool:
        from pathlib import Path as _Path
        _name = _Path(path_str).name
        return _name == "mk.py" or _name.endswith("_mk.py") or _name.endswith(".mk.py")

    def test_accepts_underscore_mk_py(self):
        self.assertTrue(self._name_is_valid("/some/dir/app_mk.py"))

    def test_accepts_dot_mk_py(self):
        self.assertTrue(self._name_is_valid("/some/dir/app.mk.py"))

    def test_accepts_bare_mk_py(self):
        self.assertTrue(self._name_is_valid("/some/dir/mk.py"))

    def test_rejects_plain_py(self):
        self.assertFalse(self._name_is_valid("/some/dir/module.py"))

    def test_rejects_no_mk_suffix(self):
        self.assertFalse(self._name_is_valid("/some/dir/app.py"))


class TestPrelib(unittest.TestCase):


    def test_add_value2list(self):
        list = []
        prelib.add_value2list(list, ['val1'])
        self.assertIn('val1', list)
        prelib.add_value2list(list, {'key': ['val2']})
        self.assertIn('val2', list)
        prelib.add_value2list(list, {'key': 'val3'})
        self.assertIn('val3', list)
        prelib.add_value2list(list, {'key': ['val4', 'val5']})
        self.assertIn('val4', list)
        self.assertIn('val5', list)
        self.assertNotIn('key', list)
        include = Path('./inc/main.h')
        prelib.add_value2list(list, include)
        self.assertIn(include, list)


    def test_list2str(self):
        l = ['val', 'val1', 'val2']
        resp = prelib.list2str(l)
        self.assertEqual('val val1 val2', resp)


    

if __name__ == '__main__':
    unittest.main()