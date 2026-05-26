"""Tests for the sort_sources and sort_modules hooks on AbstractMake and ProjectConfig."""
import unittest
from pathlib import Path

from pymakelib import AbstractMake, ProjectConfig


class _MinimalMake(AbstractMake):
    """Minimal concrete subclass that uses the default sort_sources."""

    def getProjectSettings(self, **_kw):
        return {}

    def getTargetsScript(self, **_kw):
        return {}

    def getCompilerSet(self, **_kw):
        return {}

    def getCompilerOpts(self, **_kw):
        return {}

    def getLinkerOpts(self, **_kw):
        return {}


class _ReverseMake(_MinimalMake):
    """AbstractMake subclass with custom sort (reverse alphabetical)."""

    def sort_sources(self, paths: list) -> list:
        return sorted(paths, key=str, reverse=True)


class TestSortSourcesDefault(unittest.TestCase):
    """Default sort_sources: alphabetical, no regression."""

    def setUp(self):
        self._instance = _MinimalMake()

    def test_default_returns_alphabetical(self):
        paths = [Path("z.c"), Path("a.c"), Path("m.c")]
        result = self._instance.sort_sources(paths)
        self.assertEqual(result, [Path("a.c"), Path("m.c"), Path("z.c")])

    def test_default_returns_list_of_paths(self):
        paths = [Path("b.c"), Path("a.c")]
        result = self._instance.sort_sources(paths)
        self.assertIsInstance(result[0], Path)

    def test_default_empty(self):
        self.assertEqual(self._instance.sort_sources([]), [])

    def test_default_single(self):
        paths = [Path("only.c")]
        self.assertEqual(self._instance.sort_sources(paths), [Path("only.c")])


class TestSortSourcesCustomAbstractMake(unittest.TestCase):
    """Custom sort_sources on an AbstractMake subclass."""

    def setUp(self):
        self._instance = _ReverseMake()

    def test_custom_sort_applied(self):
        paths = [Path("a.c"), Path("z.c"), Path("m.c")]
        result = self._instance.sort_sources(paths)
        self.assertEqual(result, [Path("z.c"), Path("m.c"), Path("a.c")])

    def test_custom_sort_returns_paths(self):
        paths = [Path("b.c"), Path("a.c")]
        result = self._instance.sort_sources(paths)
        self.assertIsInstance(result[0], Path)


class TestSortSourcesProjectConfig(unittest.TestCase):
    """ProjectConfig subclass with sort_sources."""

    def test_default_inherited(self):
        class _Cfg(ProjectConfig):
            name = "test"
            compiler_set = None

            def getCompilerSet(self, **_kw):
                return {}

            def getTargetsScript(self, **_kw):
                return {}

            def getLinkerOpts(self, **_kw):
                return {}

        inst = _Cfg()
        paths = [Path("z.c"), Path("a.c")]
        result = inst.sort_sources(paths)
        self.assertEqual(result, [Path("a.c"), Path("z.c")])

    def test_override_on_subclass(self):
        class _Cfg(ProjectConfig):
            name = "test"
            compiler_set = None

            def getCompilerSet(self, **_kw):
                return {}

            def getTargetsScript(self, **_kw):
                return {}

            def getLinkerOpts(self, **_kw):
                return {}

            def sort_sources(self, paths):
                return list(reversed(paths))

        inst = _Cfg()
        paths = [Path("a.c"), Path("b.c"), Path("c.c")]
        result = inst.sort_sources(paths)
        self.assertEqual(result, [Path("c.c"), Path("b.c"), Path("a.c")])


def _mplab_walk(paths: list) -> list:
    """Minimal replica of mplab_walk: dirs-before-files, depth-first, case-insensitive."""
    tree: dict = {}
    for p in paths:
        node = tree
        parts = p.parts
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        node[parts[-1]] = p

    def flatten(node: dict) -> list:
        dir_names = sorted(
            (k for k, v in node.items() if isinstance(v, dict)), key=str.lower
        )
        file_names = sorted(
            (k for k, v in node.items() if not isinstance(v, dict)), key=str.lower
        )
        out = []
        for name in dir_names:
            out.extend(flatten(node[name]))
        for name in file_names:
            out.append(node[name])
        return out

    return flatten(tree)


class TestMplabWalkStyle(unittest.TestCase):
    """MPLAB walk sort pattern: dirs before files, depth-first."""

    def test_dirs_before_files(self):
        paths = [Path("main.c"), Path("sub/foo.c"), Path("sub/bar.c")]
        result = _mplab_walk(paths)
        self.assertEqual(result, [Path("sub/bar.c"), Path("sub/foo.c"), Path("main.c")])

    def test_nested_dirs(self):
        paths = [Path("a.c"), Path("sub/b.c"), Path("sub/deep/c.c")]
        result = _mplab_walk(paths)
        self.assertEqual(result, [Path("sub/deep/c.c"), Path("sub/b.c"), Path("a.c")])

    def test_empty(self):
        self.assertEqual(_mplab_walk([]), [])

    def test_sort_sources_with_mplab_walk(self):
        class _Cfg(ProjectConfig):
            name = "test"
            compiler_set = None

            def getCompilerSet(self, **_kw):
                return {}

            def getTargetsScript(self, **_kw):
                return {}

            def getLinkerOpts(self, **_kw):
                return {}

            def sort_sources(self, paths):
                return _mplab_walk(paths)

        inst = _Cfg()
        paths = [Path("main.c"), Path("drivers/uart.c"), Path("drivers/spi.c")]
        result = inst.sort_sources(paths)
        self.assertEqual(
            result, [Path("drivers/spi.c"), Path("drivers/uart.c"), Path("main.c")]
        )


class TestSortModulesDefault(unittest.TestCase):
    """Default sort_modules: alphabetical by path, no regression."""

    def setUp(self):
        self._instance = _MinimalMake()

    def test_default_sorts_alphabetically(self):
        paths = [Path("z_mk.py"), Path("a_mk.py"), Path("m_mk.py")]
        result = self._instance.sort_modules(paths)
        self.assertEqual(result, [Path("a_mk.py"), Path("m_mk.py"), Path("z_mk.py")])

    def test_default_empty(self):
        self.assertEqual(self._instance.sort_modules([]), [])

    def test_default_single(self):
        paths = [Path("app_mk.py")]
        self.assertEqual(self._instance.sort_modules(paths), [Path("app_mk.py")])

    def test_default_returns_paths(self):
        paths = [Path("app_mk.py")]
        result = self._instance.sort_modules(paths)
        self.assertIsInstance(result[0], Path)


class TestSortModulesCustom(unittest.TestCase):
    """Custom sort_modules on AbstractMake and ProjectConfig subclasses."""

    def test_custom_sort_by_stem(self):
        class _Cfg(_MinimalMake):
            def sort_modules(self, paths):
                return sorted(paths, key=lambda p: p.stem)

        inst = _Cfg()
        paths = [Path("z_mk.py"), Path("a_mk.py"), Path("m_mk.py")]
        result = inst.sort_modules(paths)
        self.assertEqual(result, [Path("a_mk.py"), Path("m_mk.py"), Path("z_mk.py")])

    def test_custom_reverse_sort(self):
        class _Cfg(ProjectConfig):
            name = "test"
            compiler_set = None

            def getCompilerSet(self, **_kw):
                return {}

            def getTargetsScript(self, **_kw):
                return {}

            def getLinkerOpts(self, **_kw):
                return {}

            def sort_modules(self, paths):
                return sorted(paths, reverse=True)

        inst = _Cfg()
        paths = [Path("app_mk.py"), Path("drivers_mk.py")]
        result = inst.sort_modules(paths)
        self.assertEqual(result, [Path("drivers_mk.py"), Path("app_mk.py")])

    def test_custom_by_depth_then_name(self):
        """Deeper paths (subdirectories) come first."""
        class _Cfg(_MinimalMake):
            def sort_modules(self, paths):
                return sorted(paths, key=lambda p: (-len(p.parts), str(p)))

        inst = _Cfg()
        paths = [
            Path("app_mk.py"),
            Path("drivers/uart_mk.py"),
            Path("drivers/bsp/led_mk.py"),
        ]
        result = inst.sort_modules(paths)
        self.assertEqual(result, [
            Path("drivers/bsp/led_mk.py"),
            Path("drivers/uart_mk.py"),
            Path("app_mk.py"),
        ])
