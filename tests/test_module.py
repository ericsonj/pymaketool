import sys
import unittest
import pytest

from pathlib import Path
from pymakelib import module
from pymakelib import preconts as K

_PROJECT_ROOT = Path(__file__).parent.parent
_THIS_MODULE = sys.modules[__name__]


def _set_project_root(root: Path):
    _THIS_MODULE._project_root = root


def _clear_project_root():
    if hasattr(_THIS_MODULE, '_project_root'):
        del _THIS_MODULE._project_root


class TestModule(unittest.TestCase):

    def setUp(self):
        _set_project_root(_PROJECT_ROOT)

    def tearDown(self):
        _clear_project_root()

    def test_src_type(self):
        self.assertIn('.c', module.SrcType.C)
        self.assertIn('.C', module.SrcType.CPP)

    def test_src_type_c_and_asm(self):
        self.assertIn('.c', module.SrcType.C_AND_ASM)
        self.assertIn('.s', module.SrcType.C_AND_ASM)
        self.assertIn('.S', module.SrcType.C_AND_ASM)
        self.assertIn('.asm', module.SrcType.C_AND_ASM)
        self.assertNotIn('.cpp', module.SrcType.C_AND_ASM)

    def test_src_type_cpp_and_asm(self):
        self.assertIn('.cpp', module.SrcType.CPP_AND_ASM)
        self.assertIn('.s', module.SrcType.CPP_AND_ASM)
        self.assertNotIn('.c', module.SrcType.CPP_AND_ASM)

    def test_inc_type(self):
        self.assertIn('.h', module.IncType.C)
        self.assertIn('.hpp', module.IncType.CPP)

    def test_basic_c_module(self):
        class ModTest(module.BasicCModule):
            pass

        mod = ModTest()
        self.assertEqual('ModTest', mod.module_name)
        self.assertIsInstance(mod.getSrcs(), list)
        self.assertIsInstance(mod.getIncs(), list)

    def test_abstract_module(self):
        class ModTest(module.AbstractModule):

            def getSrcs(self) -> list:
                return ['mod/src/main.c']

            def getIncs(self) -> list:
                return ['mod/inc/main.h']

        mod = ModTest()
        self.assertEqual('ModTest', mod.module_name)
        self.assertIsInstance(mod.getSrcs(), list)
        self.assertIsInstance(mod.getIncs(), list)


class TestAbstractModuleMeta(unittest.TestCase):

    def setUp(self):
        _set_project_root(_PROJECT_ROOT)

    def tearDown(self):
        _clear_project_root()

    def test_get_module_name_returns_class_name(self):
        class MyNamedMod(module.AbstractModule):
            def getSrcs(self): return []
            def getIncs(self): return []

        mod = MyNamedMod()
        self.assertEqual('MyNamedMod', mod.get_module_name())

    def test_get_path_contains_class_name(self):
        class MyPathMod(module.AbstractModule):
            def getSrcs(self): return []
            def getIncs(self): return []

        mod = MyPathMod()
        self.assertIn('MyPathMod', mod.get_path())


class TestBasicCModuleFs(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path
        _set_project_root(tmp_path)
        yield
        _clear_project_root()

    def test_getSrcs_discovers_c_files(self):
        tmp = self.tmp_path
        (tmp / "main.c").write_text("")
        (tmp / "utils.c").write_text("")

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        srcs = mod.getSrcs()
        self.assertEqual(2, len(srcs))
        self.assertTrue(all(s.endswith('.c') for s in srcs))

    def test_getSrcs_discovers_asm_files(self):
        tmp = self.tmp_path
        (tmp / "main.c").write_text("")
        (tmp / "startup.s").write_text("")
        (tmp / "vectors.S").write_text("")

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        srcs = mod.getSrcs()
        self.assertEqual(3, len(srcs))
        exts = {s.rsplit('.', 1)[-1] for s in srcs}
        self.assertIn('c', exts)
        self.assertIn('s', exts)
        self.assertIn('S', exts)

    def test_getIncs_returns_module_path(self):
        tmp = self.tmp_path

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        incs = mod.getIncs()
        self.assertEqual([mod.module_path], incs)

    def test_getIncs_discovers_header_dirs_by_default(self):
        tmp = self.tmp_path
        (tmp / "inc").mkdir()
        (tmp / "inc" / "public.h").write_text("")
        (tmp / "inc" / "private").mkdir()
        (tmp / "inc" / "private" / "detail.hpp").write_text("")

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        incs = mod.getIncs()
        self.assertIn(mod.module_path + "inc", incs)
        self.assertIn(mod.module_path + "inc/private", incs)

    def test_findSrcs_cpp_discovers_cpp_files(self):
        tmp = self.tmp_path
        (tmp / "lib.cpp").write_text("")
        (tmp / "main.cc").write_text("")

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        srcs = mod.findSrcs(module.SrcType.CPP)
        self.assertEqual(2, len(srcs))

    def test_findIncs_cpp_discovers_hpp_directories(self):
        tmp = self.tmp_path
        inc_dir = tmp / "inc"
        inc_dir.mkdir()
        (inc_dir / "algo.hpp").write_text("")

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        mod = ModTest()
        incs = mod.findIncs(module.IncType.CPP)
        self.assertIn(inc_dir, incs)


class TestAbstractModuleNewHelpers(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path
        _set_project_root(tmp_path)
        yield
        _clear_project_root()

    def _make_mod(self):
        tmp = self.tmp_path

        class ModTest(module.BasicCModule):
            #pylint: disable=no-self-argument
            def get_path(_self):
                return str(tmp / "mod_mk.py")

        return ModTest()

    def test_discover_srcs_returns_strings(self):
        (self.tmp_path / "main.c").write_text("")
        mod = self._make_mod()
        srcs = mod.discover_srcs()
        self.assertTrue(all(isinstance(s, str) for s in srcs))

    def test_discover_srcs_includes_c_and_asm(self):
        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "isr.s").write_text("")
        mod = self._make_mod()
        srcs = mod.discover_srcs()
        self.assertEqual(2, len(srcs))

    def test_discover_srcs_custom_type(self):
        (self.tmp_path / "main.c").write_text("")
        (self.tmp_path / "lib.cpp").write_text("")
        mod = self._make_mod()
        srcs = mod.discover_srcs(module.SrcType.CPP)
        self.assertEqual(1, len(srcs))
        self.assertTrue(srcs[0].endswith('.cpp'))

    def test_discover_incs_returns_list(self):
        mod = self._make_mod()
        incs = mod.discover_incs()
        self.assertIsInstance(incs, list)

    def test_srcs_from_prefixes_module_path(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        result = mod.srcs_from(["main.c", "util.c"])
        self.assertEqual(["app/main.c", "app/util.c"], result)

    def test_incs_from_prefixes_module_path(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        result = mod.incs_from(["include/"])
        self.assertEqual(["app/include/"], result)

    def test_incs_from_none_returns_module_path(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        result = mod.incs_from()
        self.assertEqual(["app/"], result)

    def test_incs_from_dot_returns_module_path(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        result = mod.incs_from(["."])
        self.assertEqual(["app/"], result)

    def test_incs_from_empty_returns_module_path(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        result = mod.incs_from([""])
        self.assertEqual(["app/"], result)

    def test_deprecated_getSrcsWithPath_warns(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        with self.assertWarns(DeprecationWarning):
            result = mod.getSrcsWithPath(["main.c"])
        self.assertEqual(["app/main.c"], result)

    def test_deprecated_getIncsWithPath_warns(self):
        mod = self._make_mod()
        mod.module_path = "app/"
        with self.assertWarns(DeprecationWarning):
            result = mod.getIncsWithPath(["inc/"])
        self.assertEqual(["app/inc/"], result)

    def test_deprecated_getAllSrcsC_warns(self):
        (self.tmp_path / "main.c").write_text("")
        mod = self._make_mod()
        with self.assertWarns(DeprecationWarning):
            result = mod.getAllSrcsC()
        self.assertEqual(1, len(result))

    def test_deprecated_getAllIncsC_warns(self):
        inc_dir = self.tmp_path / "inc"
        inc_dir.mkdir()
        (inc_dir / "header.h").write_text("")
        mod = self._make_mod()
        with self.assertWarns(DeprecationWarning):
            result = mod.getAllIncsC()
        self.assertIn(inc_dir, result)


class TestCompilerOptions(unittest.TestCase):

    def test_setOption_replaces_value(self):
        co = module.CompilerOptions({'flags': ['-O0']})
        co.setOption('flags', ['-O2'])
        self.assertEqual(['-O2'], co.opts['flags'])

    def test_addOption_appends_string(self):
        co = module.CompilerOptions({'flags': ['-O0']})
        co.addOption('flags', '-Wall')
        self.assertIn('-Wall', co.opts['flags'])

    def test_addOption_extends_with_list(self):
        co = module.CompilerOptions({'flags': ['-O0']})
        co.addOption('flags', ['-Wall', '-Werror'])
        self.assertIn('-Wall', co.opts['flags'])
        self.assertIn('-Werror', co.opts['flags'])

    def test_addOption_creates_new_key(self):
        co = module.CompilerOptions({})
        co.addOption('newkey', 'value')
        self.assertEqual('value', co.opts['newkey'])


class TestGCCCompilerOpts(unittest.TestCase):

    def _make_gcc(self):
        return module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}})

    def test_addMacroOpts_adds_macro(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('DEBUG')
        self.assertIn('DEBUG', gcc.opts[K.MK_KEY_MACROS])

    def test_addMacroOpts_with_value(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('VERSION', '2')
        self.assertEqual('2', gcc.getMacroValue('VERSION'))

    def test_isDefine_true(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('NDEBUG')
        self.assertTrue(gcc.isDefine('NDEBUG'))

    def test_isDefine_false(self):
        gcc = self._make_gcc()
        self.assertFalse(gcc.isDefine('MISSING'))

    def test_isMacroValue_true(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('LEVEL', '3')
        self.assertTrue(gcc.isMacroValue('LEVEL', '3'))

    def test_isMacroValue_wrong_value(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('LEVEL', '3')
        self.assertFalse(gcc.isMacroValue('LEVEL', '99'))

    def test_addMacroOpts_value_with_spaces(self):
        gcc = self._make_gcc()
        gcc.addMacroOpts('LABEL', 'hello world')
        self.assertEqual('hello world', gcc.getMacroValue('LABEL'))

    def test_isMacroValue_undefined_macro(self):
        gcc = self._make_gcc()
        self.assertFalse(gcc.isMacroValue('MISSING', 'x'))


class TestStaticLibrary(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_construction_sets_name_and_lib_name(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path))
        self.assertEqual('mylib', lib.name)
        self.assertEqual('libmylib.a', lib.lib_name)
        self.assertFalse(lib.rebuild)

    def test_setRebuild_changes_flag(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path))
        lib.setRebuild(True)
        self.assertTrue(lib.rebuild)

    def test_rebuildByCheckStr_first_call_triggers_rebuild(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path))
        lib.rebuildByCheckStr("content_v1")
        self.assertTrue(lib.rebuild)

    def test_rebuildByCheckStr_same_content_does_not_rebuild(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path))
        lib.rebuildByCheckStr("same_content")
        lib.setRebuild(False)
        lib.rebuildByCheckStr("same_content")
        self.assertFalse(lib.rebuild)

    def test_rebuildByCheckStr_changed_content_triggers_rebuild(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path))
        lib.rebuildByCheckStr("content_v1")
        lib.setRebuild(False)
        lib.rebuildByCheckStr("content_v2")
        self.assertTrue(lib.rebuild)


class TestModuleHandle(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def _make_handle(self):
        return module.ModuleHandle(str(self.tmp_path), {})

    def test_getAllSrcsC_returns_c_files(self):
        (self.tmp_path / "main.c").write_text("")
        h = self._make_handle()
        srcs = h.getAllSrcsC()
        self.assertEqual(1, len(srcs))
        self.assertEqual('.c', srcs[0].suffix)

    def test_getFilesByRegex_matches_pattern(self):
        (self.tmp_path / "foo.c").write_text("")
        (self.tmp_path / "bar.h").write_text("")
        h = self._make_handle()
        result = h.getFilesByRegex(['*.c'])
        self.assertEqual(1, len(result))
        self.assertEqual('.c', result[0].suffix)

    def test_getSrcsByPath_prepends_modDir(self):
        h = self._make_handle()
        result = h.getSrcsByPath(['src/main.c'])
        self.assertEqual(1, len(result))
        self.assertTrue(str(result[0]).startswith(str(self.tmp_path)))


class TestModuleClassDecorator(unittest.TestCase):

    def setUp(self):
        _set_project_root(_PROJECT_ROOT)
        module.cleanModuleInstance()

    def tearDown(self):
        _clear_project_root()
        module.cleanModuleInstance()

    def test_decorator_appends_instance(self):
        @module.ModuleClass
        class MyDecMod(module.BasicCModule):
            pass

        instances = module.getModuleInstance()
        self.assertIsNotNone(instances)
        self.assertEqual(1, len(instances))
        self.assertEqual('MyDecMod', type(instances[0]).__name__)

    def test_multiple_decorators_append_all(self):
        @module.ModuleClass
        class DecMod1(module.BasicCModule):
            pass

        @module.ModuleClass
        class DecMod2(module.BasicCModule):
            pass

        instances = module.getModuleInstance()
        self.assertEqual(2, len(instances))

    def test_clean_resets_instances(self):
        @module.ModuleClass
        class DecMod3(module.BasicCModule):
            pass

        module.cleanModuleInstance()
        instances = module.getModuleInstance()
        self.assertEqual(0, len(instances))


class TestStaticLibraryLinkedOpts(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_lib_linked_opts_as_string(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path), lib_linked_opts='-lm')
        self.assertIn('-lm', lib.lib_linked)

    def test_lib_linked_opts_as_list(self):
        lib = module.StaticLibrary('mylib', str(self.tmp_path), lib_linked_opts=['-lm', '-lc'])
        self.assertIn('-lm', lib.lib_linked)
        self.assertIn('-lc', lib.lib_linked)


class TestModuleDataClass(unittest.TestCase):

    def test_constructor_without_static_lib(self):
        mod = module.Module(['src/a.c'], ['inc/'], {}, 'app.c')
        self.assertEqual('', mod.module_name)
        self.assertEqual(0, mod.orden)

    def test_constructor_with_static_lib_orden(self):
        class FakeLib:
            orden = 5
        mod = module.Module([], [], {}, 'app.c', staticLib=FakeLib())
        self.assertEqual(5, mod.orden)

    def test_isEmpty_true_when_no_srcs_incs_lib(self):
        mod = module.Module([], [], {}, 'app.c')
        self.assertTrue(mod.isEmpty())

    def test_isEmpty_false_when_has_srcs(self):
        mod = module.Module(['src/a.c'], [], {}, 'app.c')
        self.assertFalse(mod.isEmpty())

    def test_getDirs_returns_unique_parent_dirs(self):
        from pathlib import Path
        mod = module.Module(['src/a.c', 'src/b.c', 'lib/c.c'], [], {}, 'app.c')
        dirs = mod.getDirs()
        self.assertIn(Path('src'), dirs)
        self.assertIn(Path('lib'), dirs)
        self.assertEqual(2, len(dirs))


class TestGCCCompilerOptsExtra(unittest.TestCase):

    def test_init_from_compiler_options_instance(self):
        co = module.CompilerOptions({K.MK_KEY_MACROS: {'FLAG': None}})
        gcc = module.GCC_CompilerOpts(co)
        self.assertEqual(co.opts, gcc.opts)

    def test_addGeneralOpt(self):
        gcc = module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}, K.MK_KEY_GENERAL_OPTS: []})
        gcc.addGeneralOpt(['-fno-common'])
        self.assertIn('-fno-common', gcc.opts[K.MK_KEY_GENERAL_OPTS])

    def test_setOptimizationOpts(self):
        gcc = module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}})
        gcc.setOptimizationOpts(['-O2'])
        self.assertEqual(['-O2'], gcc.opts[K.MK_KEY_OPTIMIZE_OPTS])

    def test_setControlCOpts(self):
        gcc = module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}})
        gcc.setControlCOpts(['-std=c99'])
        self.assertEqual(['-std=c99'], gcc.opts[K.MK_KEY_CONTROL_C_OPTS])

    def test_setDebuggingOpts(self):
        gcc = module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}})
        gcc.setDebuggingOpts(['-g'])
        self.assertEqual(['-g'], gcc.opts[K.MK_KEY_DEBUGGING_OPTS])

    def test_setWarningdOpts(self):
        gcc = module.GCC_CompilerOpts({K.MK_KEY_MACROS: {}})
        gcc.setWarningdOpts(['-Wall'])
        self.assertEqual(['-Wall'], gcc.opts[K.MK_KEY_WARNINGS_OPTS])


class TestModuleHandleExtra(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def _make_handle(self, goal=None):
        return module.ModuleHandle(str(self.tmp_path), {}, goal=goal)

    def test_getWorkspace_contains_expected_keys(self):
        h = self._make_handle()
        wk = h.getWorkspace()
        self.assertIn(K.MOD_WORKSPACE, wk)
        self.assertIn(K.MOD_COMPILER_OPTS, wk)
        self.assertEqual(str(self.tmp_path), wk[K.MOD_WORKSPACE])

    def test_getAllIncsC_finds_h_directories(self):
        inc_dir = self.tmp_path / 'inc'
        inc_dir.mkdir()
        (inc_dir / 'header.h').write_text('')
        h = self._make_handle()
        incs = h.getAllIncsC()
        self.assertIn(inc_dir, incs)

    def test_getFileByNames_delegates_to_regex(self):
        (self.tmp_path / 'main.c').write_text('')
        h = self._make_handle()
        result = h.getFileByNames(['*.c'])
        self.assertEqual(1, len(result))

    def test_getGeneralCompilerOpts_returns_compiler_options(self):
        h = self._make_handle()
        self.assertIsInstance(h.getGeneralCompilerOpts(), module.CompilerOptions)

    def test_getRelaptivePath_returns_modDir(self):
        h = self._make_handle()
        self.assertEqual(str(self.tmp_path), h.getRelaptivePath())

    def test_getGoal_returns_provided_goal(self):
        h = self._make_handle(goal='release')
        self.assertEqual('release', h.getGoal())

    def test_str_contains_modDir(self):
        h = self._make_handle()
        self.assertIn(str(self.tmp_path), str(h))

    def test_getFilesByRegex_with_relative_path(self):
        sub = self.tmp_path / 'sub'
        sub.mkdir()
        (sub / 'file.c').write_text('')
        h = self._make_handle()
        result = h.getFilesByRegex(['*.c'], relativePath='sub')
        self.assertEqual(1, len(result))


class TestAbstractModuleInit(unittest.TestCase):

    def setUp(self):
        _set_project_root(_PROJECT_ROOT)

    def tearDown(self):
        _clear_project_root()

    def test_init_returns_none(self):
        class ModTest(module.AbstractModule):
            def getSrcs(self): return []
            def getIncs(self): return []

        mod = ModTest()
        self.assertIsNone(mod.init())


class TestStaticLibraryModuleDecorate(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _tmp_path(self, tmp_path):
        self.tmp_path = tmp_path

    def _make_lib(self, linker_opts=None):
        tmp = self.tmp_path

        class ConcreteLib(module.StaticLibraryModule):
            def get_lib_name(self):
                return 'testlib'

            def get_lib_outputdir(self):
                return str(tmp)

            def get_linker_opts(self):
                return linker_opts

        return ConcreteLib()

    def test_decorate_module_sets_name_and_lib_name(self):
        lib = self._make_lib()
        lib.decorate_module()
        self.assertEqual('testlib', lib.name)
        self.assertEqual('libtestlib.a', lib.lib_name)

    def test_decorate_module_sets_linker(self):
        lib = self._make_lib()
        lib.decorate_module()
        self.assertIn('testlib', lib.linker)

    def test_decorate_module_linker_opts_string(self):
        lib = self._make_lib(linker_opts='-lm')
        lib.decorate_module()
        self.assertIn('testlib', lib.linker)

    def test_decorate_module_linker_opts_list(self):
        lib = self._make_lib(linker_opts=['-lm', '-lc'])
        lib.decorate_module()
        self.assertIn('testlib', lib.linker)

    def test_get_order_default(self):
        lib = self._make_lib()
        self.assertEqual(1, lib.get_order())

    def test_get_rebuild_default(self):
        lib = self._make_lib()
        self.assertFalse(lib.get_rebuild())

    def test_get_objects_returns_string(self):
        lib = self._make_lib()
        result = lib.get_objects('MYLIB')
        self.assertIn('MYLIB', result)

    def test_get_rule_returns_string(self):
        lib = self._make_lib()
        result = lib.get_rule('MYLIB')
        self.assertIn('MYLIB', result)

    def test_get_command_returns_string(self):
        lib = self._make_lib()
        result = lib.get_command('MYLIB')
        self.assertIn('MYLIB', result)


class TestModuleClassNonAbstractWarning(unittest.TestCase):

    def setUp(self):
        module.cleanModuleInstance()

    def tearDown(self):
        module.cleanModuleInstance()

    def test_decorator_on_non_abstract_module_still_appends(self):
        class PlainClass:
            pass

        module.ModuleClass(PlainClass)
        instances = module.getModuleInstance()
        self.assertEqual(1, len(instances))
        self.assertIsInstance(instances[0], PlainClass)


if __name__ == '__main__':
    unittest.main()
