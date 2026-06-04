"""Tests for the pm package — functional API + re-exports."""

import unittest
import pytest
import sys


class TestMkFunction(unittest.TestCase):
    """The mk function must be importable and callable."""

    def test_mk_is_callable(self):
        from pm import mk
        self.assertTrue(callable(mk))

    def test_mk_has_docstring(self):
        from pm import mk
        self.assertIn("module", mk.__doc__.lower())


class TestMkReExports(unittest.TestCase):
    """mk must re-export functional and class-based API."""

    def test_add_library_available(self):
        from pm import add_library
        self.assertTrue(callable(add_library))

    def test_simple_module_available(self):
        from pm import simple_module
        self.assertTrue(callable(simple_module))

    def test_basic_c_module_available(self):
        from pm import BasicCModule
        from pymakelib.module import BasicCModule as Original
        self.assertIs(BasicCModule, Original)

    def test_basic_cpp_module_available(self):
        from pm import BasicCppModule
        from pymakelib.module import BasicCppModule as Original
        self.assertIs(BasicCppModule, Original)

    def test_module_class_decorator_available(self):
        from pm import ModuleClass
        from pymakelib.module import ModuleClass as Original
        self.assertIs(ModuleClass, Original)

    def test_abstract_module_available(self):
        from pm import AbstractModule
        from pymakelib.module import AbstractModule as Original
        self.assertIs(AbstractModule, Original)

    def test_static_library_module_available(self):
        from pm import StaticLibraryModule
        from pymakelib.module import StaticLibraryModule as Original
        self.assertIs(StaticLibraryModule, Original)

    def test_src_type_available(self):
        from pm import SrcType
        from pymakelib.module import SrcType as Original
        self.assertIs(SrcType, Original)

    def test_inc_type_available(self):
        from pm import IncType
        from pymakelib.module import IncType as Original
        self.assertIs(IncType, Original)


class TestMkCallableRegistration(unittest.TestCase):
    """mk() must register a module with correct caller file detection."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_mk_callable_registers_module_with_correct_path(self):
        """The registered module's path must point to the calling file, not mk/__init__.py."""
        from pymakelib import prelib

        # Create a mk.py that uses the new import syntax
        (self.tmp_path / "main.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text("from pm import mk\nmk()\n")

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))

        # The module's filename must be the mk.py file, NOT mk/__init__.py
        module_filename = str(modules[0].filename)
        self.assertIn("mk.py", module_filename)
        self.assertNotIn("__init__", module_filename)

    def test_mk_callable_with_explicit_incs(self):
        """mk(incs=[...]) must pass includes correctly."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "inc").mkdir()
        (self.tmp_path / "inc" / "header.h").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text('from pm import mk\nmk(incs=["inc"])\n')

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        incs = [str(i) for i in modules[0].incs]
        self.assertTrue(any("inc" in i for i in incs))

    def test_mk_callable_with_explicit_srcs(self):
        """mk(srcs=[...]) must pass sources correctly."""
        from pymakelib import prelib

        (self.tmp_path / "foo.c").write_text("")
        (self.tmp_path / "bar.c").write_text("")  # should NOT be included
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text('from pm import mk\nmk(srcs=["foo.c"])\n')

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("foo.c" in s for s in srcs))
        # bar.c should NOT be auto-discovered since srcs is explicit
        self.assertFalse(any("bar.c" in s for s in srcs))

    def test_mk_callable_with_lang_cpp(self):
        """mk(lang='cpp') must register a C++ module."""
        from pymakelib import prelib

        (self.tmp_path / "main.cpp").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text('from pm import mk\nmk(lang="cpp")\n')

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.cpp" in s for s in srcs))

    def test_mk_callable_with_lang_cpp_alias(self):
        """mk(lang='c++') must work as alias for 'cpp'."""
        from pymakelib import prelib

        (self.tmp_path / "main.cpp").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text('from pm import mk\nmk(lang="c++")\n')

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.cpp" in s for s in srcs))

    def test_mk_callable_with_lang_case_insensitive(self):
        """mk(lang='CPP') must work (case-insensitive)."""
        from pymakelib import prelib

        (self.tmp_path / "main.cpp").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text('from pm import mk\nmk(lang="CPP")\n')

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.cpp" in s for s in srcs))

    def test_mk_callable_with_invalid_lang_raises(self):
        """mk(lang='invalid') must raise ValueError."""
        from pm import mk
        with self.assertRaises(ValueError) as ctx:
            mk(lang="invalid")
        self.assertIn("invalid", str(ctx.exception))


class TestMkAllExports(unittest.TestCase):
    """pm.__all__ must list all public exports."""

    def test_all_contains_expected_names(self):
        import pm
        expected = {
            "mk",
            "add_library",
            "simple_module",
            "find_srcs",
            "find_incs",
            "skip",
            "AbstractModule",
            "BasicCModule",
            "BasicCppModule",
            "ModuleClass",
            "StaticLibraryModule",
            "ExternalModule",
            "POJOModule",
            "SrcType",
            "IncType",
        }
        self.assertTrue(expected.issubset(set(pm.__all__)))


class TestFindSrcsFunction(unittest.TestCase):
    """Tests for find_srcs() — source discovery with exclude patterns."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_find_srcs_is_importable(self):
        from pm import find_srcs
        self.assertTrue(callable(find_srcs))

    def test_find_srcs_discovers_c_files(self):
        """find_srcs() must discover .c files in the caller's directory."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "util.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            "mk(srcs=find_srcs())\n"
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(1, len(modules))
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertTrue(any("util.c" in s for s in srcs))

    def test_find_srcs_excludes_by_filename_pattern(self):
        """find_srcs(exclude=['test*']) must skip files starting with 'test'."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_main.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            'mk(srcs=find_srcs(exclude=["test*"]))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_main.c" in s for s in srcs))

    def test_find_srcs_excludes_by_directory_pattern(self):
        """find_srcs(exclude=['test*']) must skip files in test* directories."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "tests").mkdir()
        (self.tmp_path / "tests" / "test_util.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            'mk(srcs=find_srcs(exclude=["test*"]))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_util.c" in s for s in srcs))

    def test_find_srcs_excludes_multiple_patterns(self):
        """find_srcs(exclude=['test*', '*.template*']) must apply all patterns."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_foo.c").write_text("")
        (self.tmp_path / "code.template.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            'mk(srcs=find_srcs(exclude=["test*", "*.template*"]))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_foo.c" in s for s in srcs))
        self.assertFalse(any("template" in s for s in srcs))

    def test_find_srcs_with_ext_cpp(self):
        """find_srcs(ext=SrcType.CPP) must discover .cpp files."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")  # should NOT be found
        (self.tmp_path / "app.cpp").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs, SrcType\n"
            'mk(srcs=find_srcs(ext=SrcType.CPP), lang="cpp")\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("app.cpp" in s for s in srcs))
        self.assertFalse(any("main.c" in s for s in srcs))

    def test_find_srcs_discovers_nested_files(self):
        """find_srcs() must recursively discover files in subdirectories."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "src").mkdir()
        (self.tmp_path / "src" / "util.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            "mk(srcs=find_srcs())\n"
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertTrue(any("util.c" in s for s in srcs))

    def test_find_srcs_empty_exclude_discovers_all(self):
        """find_srcs(exclude=[]) must discover all files (same as no exclude)."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs\n"
            "mk(srcs=find_srcs(exclude=[]))\n"
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertTrue(any("test.c" in s for s in srcs))


class TestFindIncsFunction(unittest.TestCase):
    """Tests for find_incs() — include directory discovery with exclude patterns."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_find_incs_is_importable(self):
        from pm import find_incs
        self.assertTrue(callable(find_incs))

    def test_find_incs_discovers_header_dirs(self):
        """find_incs() must discover directories containing headers."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "main.h").write_text("")
        (self.tmp_path / "inc").mkdir()
        (self.tmp_path / "inc" / "util.h").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs, find_incs\n"
            "mk(srcs=find_srcs(), incs=find_incs())\n"
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        incs = [str(i) for i in modules[0].incs]
        # Should have module root (.) and inc/ subdirectory
        self.assertTrue(len(incs) >= 1)

    def test_find_incs_excludes_by_directory_pattern(self):
        """find_incs(exclude=['test*']) must skip test* directories."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "inc").mkdir()
        (self.tmp_path / "inc" / "util.h").write_text("")
        (self.tmp_path / "test_inc").mkdir()
        (self.tmp_path / "test_inc" / "mock.h").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, find_srcs, find_incs\n"
            'mk(srcs=find_srcs(), incs=find_incs(exclude=["test*"]))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        incs = [str(i) for i in modules[0].incs]
        self.assertTrue(any("inc" in i for i in incs))
        self.assertFalse(any("test_inc" in i for i in incs))

    def test_find_incs_returns_dot_when_no_headers(self):
        """find_incs() must return ['.'] when no headers found."""
        from pymakelib.pym import _discover_includes
        from pymakelib.module import IncType
        from pathlib import Path

        # Empty directory - no headers
        result = _discover_includes(self.tmp_path, IncType.C, None)
        self.assertEqual(["."], result)


class TestSkipFunction(unittest.TestCase):
    """Tests for skip() — returns exclude dict."""

    def test_skip_returns_dict(self):
        from pm import skip
        result = skip("test*", ".template")
        self.assertEqual({"exclude": ["test*", ".template"]}, result)

    def test_skip_single_pattern(self):
        from pm import skip
        result = skip("test*")
        self.assertEqual({"exclude": ["test*"]}, result)

    def test_skip_no_patterns(self):
        from pm import skip
        result = skip()
        self.assertEqual({"exclude": []}, result)

    def test_skip_is_importable(self):
        from pm import skip
        self.assertTrue(callable(skip))


class TestMkWithSkip(unittest.TestCase):
    """Tests for mk() with skip()/dict exclude patterns."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_mk_with_skip_excludes_files(self):
        """mk(srcs=skip('test*')) must exclude files matching pattern."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_main.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*"))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_main.c" in s for s in srcs))

    def test_mk_with_dict_excludes_files(self):
        """mk(srcs={"exclude": [...]}) must work like skip()."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_main.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk\n"
            'mk(srcs={"exclude": ["test*"]})\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_main.c" in s for s in srcs))

    def test_mk_with_skip_excludes_directories(self):
        """mk(srcs=skip('test*')) must exclude files inside matching dirs."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "tests").mkdir()
        (self.tmp_path / "tests" / "check.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*"))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("check.c" in s for s in srcs))

    def test_mk_with_skip_and_explicit_incs(self):
        """mk(srcs=skip(...), incs=[...]) must combine correctly."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_util.c").write_text("")
        (self.tmp_path / "include").mkdir()
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*"), incs=[".", "include"])\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_util" in s for s in srcs))
        incs = [str(i) for i in modules[0].incs]
        self.assertTrue(any("include" in i for i in incs))

    def test_mk_with_skip_and_lang_cpp(self):
        """mk(srcs=skip(...), lang='cpp') must discover .cpp files only."""
        from pymakelib import prelib

        (self.tmp_path / "main.cpp").write_text("")
        (self.tmp_path / "main.c").write_text("")  # must NOT be found
        (self.tmp_path / "test_util.cpp").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*"), lang="cpp")\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.cpp" in s for s in srcs))
        self.assertFalse(any("main.c" in s and "main.cpp" not in s for s in srcs))
        self.assertFalse(any("test_util" in s for s in srcs))

    def test_mk_with_skip_multiple_patterns(self):
        """mk(srcs=skip('test*', '*.template*')) must apply all patterns."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "test_foo.c").write_text("")
        (self.tmp_path / "code.template.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*", "*.template*"))\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        srcs = [str(s) for s in modules[0].srcs]
        self.assertTrue(any("main.c" in s for s in srcs))
        self.assertFalse(any("test_foo" in s for s in srcs))
        self.assertFalse(any("template" in s for s in srcs))

    def test_mk_with_dict_incs_exclude(self):
        """mk(incs={"exclude": [...]}) must exclude include directories."""
        from pymakelib import prelib

        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "inc").mkdir()
        (self.tmp_path / "inc" / "util.h").write_text("")
        (self.tmp_path / "test_inc").mkdir()
        (self.tmp_path / "test_inc" / "mock.h").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text(
            "from pm import mk, skip\n"
            'mk(srcs=skip("test*"), incs={"exclude": ["test*"]})\n'
        )

        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        incs = [str(i) for i in modules[0].incs]
        self.assertTrue(any("inc" in i for i in incs))
        self.assertFalse(any("test_inc" in i for i in incs))


class TestSkipPatternRetention(unittest.TestCase):
    """skip()/dict exclude patterns must be retained on the module, prefixed
    with the module path, for emission into srcs.mk."""

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def _write_mk(self, body):
        (self.tmp_path / "main.c").write_text("")
        mk_file = self.tmp_path / "mk.py"
        mk_file.write_text("from pm import mk, skip, find_srcs\n" + body)
        return mk_file

    def test_skip_srcs_retained_and_prefixed(self):
        from pymakelib import prelib
        mk_file = self._write_mk('mk(srcs=skip("test*"))\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_srcs_patterns, ["./test*"])

    def test_skip_dict_form_retained(self):
        from pymakelib import prelib
        mk_file = self._write_mk('mk(srcs={"exclude": ["test*", "mock_*"]})\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_srcs_patterns, ["./test*", "./mock_*"])

    def test_skip_incs_retained_and_prefixed(self):
        from pymakelib import prelib
        mk_file = self._write_mk('mk(incs=skip("internal*"))\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_incs_patterns, ["./internal*"])

    def test_explicit_list_retains_nothing(self):
        from pymakelib import prelib
        mk_file = self._write_mk('mk(srcs=["main.c"])\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_srcs_patterns, [])
        self.assertEqual(modules[0].skip_incs_patterns, [])

    def test_bare_mk_retains_nothing(self):
        from pymakelib import prelib
        mk_file = self._write_mk('mk()\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_srcs_patterns, [])

    def test_find_srcs_exclude_not_retained(self):
        """find_srcs(exclude=...) collapses before mk() sees it — documented limitation."""
        from pymakelib import prelib
        (self.tmp_path / "test_x.c").write_text("")
        mk_file = self._write_mk('mk(srcs=find_srcs(exclude=["test*"]))\n')
        modules = prelib.readModule(mk_file, {}, project_root=self.tmp_path)
        self.assertEqual(modules[0].skip_srcs_patterns, [])
