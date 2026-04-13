import json
import tempfile
import unittest
from pathlib import Path

from pymakelib import Define
from pymakelib.clangd_addon import (
    CompileCommandsAddon,
    _build_flags,
    _filter_flags,
    _macros_to_args,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal projectSettings / compilerSettings dicts
# ---------------------------------------------------------------------------

def _make_settings(tmpdir: str, srcs=None, symbols=None, includes=None, compiler_opts=None):
    return {
        "C_SETTINGS": {"PROJECT_NAME": "test", "FOLDER_OUT": "build"},
        "C_TARGETS": {},
        "C_INCLUDES": includes or [],
        "C_SYMBOLS": symbols or {},
        "C_EXCLUDE": [],
        "C_SRCS": srcs or [],
        "C_COMPILER_OPTS": compiler_opts or {},
        "C_CONFIG_DIR": tmpdir,
    }


def _make_compiler_settings(cc="arm-none-eabi-gcc", cxx=None):
    s = {"CC": cc, "LD": "arm-none-eabi-ld", "AR": "arm-none-eabi-ar", "INCLUDES": []}
    if cxx:
        s["CXX"] = cxx
    return s


# ---------------------------------------------------------------------------
# Tests for _macros_to_args
# ---------------------------------------------------------------------------

class TestMacrosToArgs(unittest.TestCase):

    def test_none_value_produces_bare_define(self):
        result = _macros_to_args({"MY_FLAG": None})
        self.assertEqual(["-DMY_FLAG"], result)

    def test_empty_string_produces_bare_define(self):
        result = _macros_to_args({"MY_FLAG": ""})
        self.assertEqual(["-DMY_FLAG"], result)

    def test_string_value_no_makefile_escaping(self):
        result = _macros_to_args({"VERSION": "1.0"})
        self.assertEqual(["-DVERSION=1.0"], result)
        # Must NOT contain backslash-escaped quotes
        self.assertNotIn("\\\"", result[0])

    def test_bool_true(self):
        result = _macros_to_args({"ENABLE_X": True})
        self.assertEqual(["-DENABLE_X=1"], result)

    def test_bool_false(self):
        result = _macros_to_args({"ENABLE_X": False})
        self.assertEqual(["-DENABLE_X=0"], result)

    def test_define_raw(self):
        result = _macros_to_args({"FILE": Define("header.h")})
        self.assertEqual(["-DFILE=header.h"], result)

    def test_integer_value(self):
        result = _macros_to_args({"LEVEL": 3})
        self.assertEqual(["-DLEVEL=3"], result)

    def test_non_dict_returns_empty(self):
        self.assertEqual([], _macros_to_args(None))
        self.assertEqual([], _macros_to_args("bad"))

    def test_multiple_macros(self):
        result = _macros_to_args({"A": None, "B": "x", "C": True})
        self.assertIn("-DA", result)
        self.assertIn("-DB=x", result)
        self.assertIn("-DC=1", result)


# ---------------------------------------------------------------------------
# Tests for _build_flags
# ---------------------------------------------------------------------------

class TestBuildFlags(unittest.TestCase):

    def test_flattens_list_values(self):
        opts = {
            "MACHINE-OPTS": ["-mcpu=cortex-m4", "-mthumb"],
            "OPTIMIZE-OPTS": ["-O2"],
        }
        result = _build_flags(opts)
        self.assertIn("-mcpu=cortex-m4", result)
        self.assertIn("-mthumb", result)
        self.assertIn("-O2", result)

    def test_skips_macros_key(self):
        opts = {"MACROS": {"FOO": None}, "GENERAL-OPTS": ["-ffunction-sections"]}
        result = _build_flags(opts)
        self.assertNotIn("-DFOO", result)
        self.assertIn("-ffunction-sections", result)

    def test_skips_targets_key(self):
        opts = {"TARGETS": {"all": {}}, "WARNINGS-OPTS": ["-Wall"]}
        result = _build_flags(opts)
        self.assertIn("-Wall", result)
        self.assertNotIn("all", result)

    def test_non_dict_returns_empty(self):
        self.assertEqual([], _build_flags(None))
        self.assertEqual([], _build_flags(["-O2"]))


# ---------------------------------------------------------------------------
# Tests for _filter_flags
# ---------------------------------------------------------------------------

class TestFilterFlags(unittest.TestCase):

    def test_no_strip_returns_all(self):
        flags = ["-O2", "-Wall", "-mcpu=cortex-m4"]
        self.assertEqual(flags, _filter_flags(flags, []))

    def test_strips_by_prefix(self):
        flags = ["-O2", "-mprocessor=PIC32MX", "-Wall"]
        result = _filter_flags(flags, ["-mprocessor"])
        self.assertNotIn("-mprocessor=PIC32MX", result)
        self.assertIn("-O2", result)
        self.assertIn("-Wall", result)

    def test_drops_next_token_for_value_consuming_flag(self):
        # -mprocessor is space-separated with its value; use strip_with_value
        flags = ["-O2", "-mprocessor", "PIC32MX470F512H", "-Wall"]
        result = _filter_flags(flags, strip=[], strip_with_value=["-mprocessor"])
        self.assertNotIn("-mprocessor", result)
        self.assertNotIn("PIC32MX470F512H", result)
        self.assertIn("-O2", result)
        self.assertIn("-Wall", result)

    def test_standalone_flag_does_not_consume_next_token(self):
        # -MP is a boolean flag; the following flag must NOT be dropped
        flags = ["-MP", "-O2"]
        result = _filter_flags(flags, strip=["-MP"])
        self.assertNotIn("-MP", result)
        self.assertIn("-O2", result)

    def test_multiple_strip_prefixes(self):
        flags = ["-mprocessor=P32", "-mdfp=/path/to/dfp", "-O2"]
        result = _filter_flags(flags, ["-mprocessor", "-mdfp"])
        self.assertEqual(["-O2"], result)

    def test_partial_prefix_strip(self):
        """A prefix like '-mprocessor' should NOT strip '-mprotected'."""
        flags = ["-mprocessor=P32", "-mprotected-mode"]
        result = _filter_flags(flags, ["-mprocessor"])
        self.assertNotIn("-mprocessor=P32", result)
        self.assertIn("-mprotected-mode", result)


# ---------------------------------------------------------------------------
# Tests for CompileCommandsAddon.init()
# ---------------------------------------------------------------------------

class TestCompileCommandsAddonInit(unittest.TestCase):

    def setUp(self):
        # Reset class-level attributes between tests
        CompileCommandsAddon.strip_flags = []
        CompileCommandsAddon.strip_flags_with_value = []

    def _run_addon(self, tmpdir, srcs, symbols=None, includes=None,
                   compiler_opts=None, cc="gcc", cxx=None):
        proj = _make_settings(tmpdir, srcs=srcs, symbols=symbols,
                               includes=includes, compiler_opts=compiler_opts)
        comp = _make_compiler_settings(cc=cc, cxx=cxx)
        addon = CompileCommandsAddon(proj, comp)
        addon.init()
        out = Path(tmpdir) / "compile_commands.json"
        return json.loads(out.read_text())

    def test_creates_compile_commands_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_addon(tmpdir, srcs=["src/main.c"])
            self.assertTrue((Path(tmpdir) / "compile_commands.json").exists())

    def test_one_entry_per_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/a.c", "src/b.c"])
            self.assertEqual(2, len(entries))

    def test_entry_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c"])
            entry = entries[0]
            self.assertIn("directory", entry)
            self.assertIn("file", entry)
            self.assertIn("arguments", entry)

    def test_c_file_uses_cc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c"], cc="arm-none-eabi-gcc")
            self.assertEqual("arm-none-eabi-gcc", entries[0]["arguments"][0])

    def test_cpp_file_uses_cxx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/app.cpp"],
                                      cc="arm-none-eabi-gcc", cxx="arm-none-eabi-g++")
            self.assertEqual("arm-none-eabi-g++", entries[0]["arguments"][0])

    def test_cpp_falls_back_to_cc_when_cxx_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/app.cpp"], cc="gcc", cxx=None)
            self.assertEqual("gcc", entries[0]["arguments"][0])

    def test_asm_file_uses_cc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["startup/reset.S"], cc="arm-none-eabi-gcc")
            self.assertEqual("arm-none-eabi-gcc", entries[0]["arguments"][0])

    def test_includes_appear_in_arguments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c"],
                                       includes=["inc/", "drivers/inc/"])
            args = entries[0]["arguments"]
            self.assertIn("-Iinc/", args)
            self.assertIn("-Idrivers/inc/", args)

    def test_macros_appear_in_arguments_without_makefile_escaping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            symbols = {"DEBUG": None, "VERSION": "2.0", "USE_HW": True}
            entries = self._run_addon(tmpdir, srcs=["src/main.c"], symbols=symbols)
            args = entries[0]["arguments"]
            self.assertIn("-DDEBUG", args)
            self.assertIn("-DVERSION=2.0", args)
            self.assertIn("-DUSE_HW=1", args)
            # No Makefile escaping
            for a in args:
                self.assertNotIn("\\\"", a)

    def test_strip_flags_applied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # -MP is standalone (no value); -mprocessor takes the next token
            CompileCommandsAddon.strip_flags = ["-MP"]
            CompileCommandsAddon.strip_flags_with_value = ["-mprocessor"]
            opts = {"MACHINE-OPTS": ["-mprocessor=PIC32MX", "-MP", "-O2"]}
            entries = self._run_addon(tmpdir, srcs=["src/main.c"], compiler_opts=opts)
            args = entries[0]["arguments"]
            self.assertIn("-O2", args)
            self.assertNotIn("-mprocessor=PIC32MX", args)
            self.assertNotIn("-MP", args)

    def test_unknown_extension_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c", "src/data.o"])
            self.assertEqual(1, len(entries))

    def test_file_path_is_absolute(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c"])
            self.assertTrue(Path(entries[0]["file"]).is_absolute())

    def test_last_argument_is_source_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=["src/main.c"])
            args = entries[0]["arguments"]
            # Format: [..., "-c", "<abs_path>"]
            self.assertEqual("-c", args[-2])
            self.assertTrue(args[-1].endswith("main.c"))

    def test_empty_sources_produces_empty_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = self._run_addon(tmpdir, srcs=[])
            self.assertEqual([], entries)


if __name__ == "__main__":
    unittest.main()
