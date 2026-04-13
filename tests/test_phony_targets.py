import unittest
import pytest

from pymakelib import prelib
from pymakelib import AbstractMake
from pymakelib.generator import PhonyTargetsGenerator


# ---------------------------------------------------------------------------
# _deps_to_str
# ---------------------------------------------------------------------------

class TestDepsToStr(unittest.TestCase):

    def test_string_passthrough(self):
        self.assertEqual('all', prelib._deps_to_str('all'))

    def test_make_variable_passthrough(self):
        self.assertEqual('$(TARGET)', prelib._deps_to_str('$(TARGET)'))

    def test_list_joined_with_space(self):
        self.assertEqual('all $(TARGET)', prelib._deps_to_str(['all', '$(TARGET)']))

    def test_empty_list_returns_empty_string(self):
        self.assertEqual('', prelib._deps_to_str([]))

    def test_none_returns_empty_string(self):
        self.assertEqual('', prelib._deps_to_str(None))


# ---------------------------------------------------------------------------
# _script_to_lines
# ---------------------------------------------------------------------------

class TestScriptToLines(unittest.TestCase):

    def test_string_returns_single_item_list(self):
        self.assertEqual(
            ['openocd -c "erase"'],
            prelib._script_to_lines('openocd -c "erase"')
        )

    def test_list_returned_as_is(self):
        cmds = ['cmd1', 'cmd2']
        self.assertEqual(cmds, prelib._script_to_lines(cmds))

    def test_empty_list_returns_empty_list(self):
        self.assertEqual([], prelib._script_to_lines([]))

    def test_none_returns_empty_list(self):
        self.assertEqual([], prelib._script_to_lines(None))


# ---------------------------------------------------------------------------
# AbstractMake.getPhonyTargets default
# ---------------------------------------------------------------------------

class TestAbstractMakePhonyDefault(unittest.TestCase):

    def _make_concrete(self):
        class ConcreteProject(AbstractMake):
            def getProjectSettings(self): return {}
            def getTargetsScript(self): return {}
            def getCompilerSet(self): return {}
            def getCompilerOpts(self): return {}
            def getLinkerOpts(self): return {}

        return ConcreteProject()

    def test_returns_empty_dict_by_default(self):
        self.assertEqual({}, self._make_concrete().getPhonyTargets())

    def test_return_type_is_dict(self):
        self.assertIsInstance(self._make_concrete().getPhonyTargets(), dict)


# ---------------------------------------------------------------------------
# PhonyTargetsGenerator
# ---------------------------------------------------------------------------

class TestPhonyTargetsGenerator(unittest.TestCase):

    def _make_generator(self, phony_targets):
        class MockProject:
            pass
        proj = MockProject()
        proj.compilerOpts = {'PHONY_TARGETS': phony_targets}
        return PhonyTargetsGenerator(proj)

    def test_empty_phony_targets_returns_empty_string(self):
        gen = self._make_generator({})
        self.assertEqual('', gen.process())

    def test_missing_phony_targets_key_returns_empty_string(self):
        class MockProject:
            compilerOpts = {}
        gen = PhonyTargetsGenerator(MockProject())
        self.assertEqual('', gen.process())

    def test_phony_declaration_lists_all_names(self):
        gen = self._make_generator({
            'flash': {'script': 'openocd'},
            'size': {'script': '$(SIZE)'},
        })
        result = gen.process()
        self.assertIn('.PHONY: flash size', result)

    def test_target_with_list_deps(self):
        gen = self._make_generator({
            'flash': {'deps': ['all'], 'script': 'openocd'}
        })
        self.assertIn('flash: all', gen.process())

    def test_target_with_string_dep(self):
        gen = self._make_generator({
            'flash': {'deps': '$(TARGET)', 'script': 'openocd'}
        })
        self.assertIn('flash: $(TARGET)', gen.process())

    def test_target_no_deps(self):
        gen = self._make_generator({
            'erase': {'script': 'openocd -c "erase"'}
        })
        result = gen.process()
        self.assertIn('erase:', result)

    def test_logkey_defaults_to_uppercase_name(self):
        gen = self._make_generator({'flash': {'script': 'openocd'}})
        self.assertIn('"FLASH"', gen.process())

    def test_logkey_custom_value(self):
        gen = self._make_generator({'flash': {'logkey': 'PROG', 'script': 'openocd'}})
        self.assertIn('"PROG"', gen.process())

    def test_script_as_string_is_single_recipe_line(self):
        gen = self._make_generator({'flash': {'script': 'openocd -c "program $(TARGET)"'}})
        result = gen.process()
        self.assertIn('\topenocd -c "program $(TARGET)"', result)

    def test_script_as_list_each_item_is_recipe_line(self):
        gen = self._make_generator({
            'test': {'script': ['pytest tests/', 'echo done']}
        })
        result = gen.process()
        self.assertIn('\tpytest tests/ \\\n', result)
        self.assertIn('\techo done\n', result)

    def test_script_as_list_single_item_no_backslash(self):
        gen = self._make_generator({'flash': {'script': ['openocd']}})
        result = gen.process()
        self.assertNotIn('\\', result)
        self.assertIn('\topenocd\n', result)

    def test_logger_compile_call_present(self):
        gen = self._make_generator({'flash': {'script': 'openocd'}})
        self.assertIn('$(call logger-compile', gen.process())


# ---------------------------------------------------------------------------
# read_Makefilepy integration
# ---------------------------------------------------------------------------

_MINIMAL_MAKEFILE_PY = """\
from pymakelib import MKVARS

def getProjectSettings():
    return {'PROJECT_NAME': 'test', 'FOLDER_OUT': 'out/'}

def getCompilerSet():
    return {'CC': 'gcc', 'CXX': 'g++', 'LD': 'gcc', 'AR': 'ar', 'AS': 'as',
            'OBJCOPY': 'objcopy', 'SIZE': 'size', 'OBJDUMP': 'objdump'}

def getCompilerOpts():
    return {'MACROS': {}, 'GENERAL-OPTS': []}

def getLinkerOpts():
    return {'LINKER-SCRIPT': [], 'MACHINE-OPTS': [], 'GENERAL-OPTS': [],
            'LINKER-OPTS': [], 'LIBRARIES': []}

def getTargetsScript():
    return {
        'TARGET': {
            'LOGKEY': 'OUT',
            'FILE': 'out/test',
            'SCRIPT': [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS]
        }
    }
"""


class TestReadMakefilePhonyIntegration:

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        self.tmp_path = tmp_path
        monkeypatch.chdir(tmp_path)

    def _write_makefile_py(self, extra=''):
        (self.tmp_path / 'Makefile.py').write_text(_MINIMAL_MAKEFILE_PY + extra)

    def _targets_mk(self):
        return (self.tmp_path / 'targets.mk').read_text()

    def test_no_phony_function_writes_no_phony_block(self):
        self._write_makefile_py()
        prelib.read_Makefilepy()
        assert '.PHONY:' not in self._targets_mk()

    def test_empty_phony_dict_writes_no_phony_block(self):
        self._write_makefile_py('\ndef getPhonyTargets():\n    return {}\n')
        prelib.read_Makefilepy()
        assert '.PHONY:' not in self._targets_mk()

    def test_phony_declaration_written(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'script': 'openocd'},
    }
""")
        prelib.read_Makefilepy()
        assert '.PHONY: flash' in self._targets_mk()

    def test_multiple_targets_all_in_phony_declaration(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'script': 'openocd'},
        'size':  {'script': '$(SIZE)'},
        'erase': {'script': 'openocd -c erase'},
    }
""")
        prelib.read_Makefilepy()
        content = self._targets_mk()
        assert '.PHONY:' in content
        assert 'flash' in content
        assert 'size' in content
        assert 'erase' in content

    def test_target_with_list_deps_written(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'deps': ['all'], 'script': 'openocd'},
    }
""")
        prelib.read_Makefilepy()
        assert 'flash: all' in self._targets_mk()

    def test_target_with_string_dep_written(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'size': {'deps': '$(TARGET)', 'script': '$(SIZE) $(TARGET)'},
    }
""")
        prelib.read_Makefilepy()
        assert 'size: $(TARGET)' in self._targets_mk()

    def test_script_as_string_written(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'erase': {'script': 'openocd -c "erase"'},
    }
""")
        prelib.read_Makefilepy()
        assert '\topenocd -c "erase"' in self._targets_mk()

    def test_script_as_list_each_item_written(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'test': {'script': ['pytest tests/', 'echo done']},
    }
""")
        prelib.read_Makefilepy()
        content = self._targets_mk()
        assert '\tpytest tests/' in content
        assert '\\\n' in content
        assert '\techo done\n' in content

    def test_script_as_list_single_item_no_backslash(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'script': ['openocd']},
    }
""")
        prelib.read_Makefilepy()
        content = self._targets_mk()
        assert '\\\n' not in content
        assert '\topenocd\n' in content

    def test_logkey_defaults_to_uppercase_name(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'script': 'openocd'},
    }
""")
        prelib.read_Makefilepy()
        assert '"FLASH"' in self._targets_mk()

    def test_logkey_custom_value_used(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'logkey': 'PROG', 'script': 'openocd'},
    }
""")
        prelib.read_Makefilepy()
        assert '"PROG"' in self._targets_mk()

    def test_phony_targets_stored_in_compiler_opts(self):
        self._write_makefile_py("""
def getPhonyTargets():
    return {
        'flash': {'script': 'openocd'},
    }
""")
        _, comp_opts, _ = prelib.read_Makefilepy()
        assert 'PHONY_TARGETS' in comp_opts
        assert 'flash' in comp_opts['PHONY_TARGETS']

    def test_phony_targets_not_in_compiler_opts_when_empty(self):
        self._write_makefile_py('\ndef getPhonyTargets():\n    return {}\n')
        _, comp_opts, _ = prelib.read_Makefilepy()
        assert 'PHONY_TARGETS' not in comp_opts


if __name__ == '__main__':
    unittest.main()
