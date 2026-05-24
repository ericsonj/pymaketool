import unittest
from pymakelib import CompilerOpts, Define


class TestCompilerOptsFluentMacros(unittest.TestCase):

    def test_define_flag_sets_none(self):
        opts = CompilerOpts().define_flag('DEBUG')
        self.assertIsNone(opts.macros['DEBUG'])

    def test_define_string_sets_value(self):
        opts = CompilerOpts().define_string('APP_NAME', 'My App')
        self.assertEqual(opts.macros['APP_NAME'], 'My App')

    def test_define_raw_sets_define_instance(self):
        opts = CompilerOpts().define_raw('HEADER', 'config.h')
        self.assertIsInstance(opts.macros['HEADER'], Define)
        self.assertEqual(str(opts.macros['HEADER']), 'config.h')

    def test_define_int_sets_integer(self):
        opts = CompilerOpts().define_int('VERSION', 3)
        self.assertEqual(opts.macros['VERSION'], 3)

    def test_chaining_all_methods(self):
        opts = (CompilerOpts()
            .define_flag('NDEBUG')
            .define_string('NAME', 'test')
            .define_raw('HDR', 'app.h')
            .define_int('LEVEL', 5))
        self.assertEqual(len(opts.macros), 4)
        self.assertIsNone(opts.macros['NDEBUG'])
        self.assertEqual(opts.macros['NAME'], 'test')
        self.assertIsInstance(opts.macros['HDR'], Define)
        self.assertEqual(opts.macros['LEVEL'], 5)

    def test_returns_self_for_chaining(self):
        opts = CompilerOpts()
        result = opts.define_flag('X')
        self.assertIs(result, opts)

    def test_to_dict_includes_macros(self):
        opts = CompilerOpts().define_flag('DEBUG').define_int('VER', 2)
        d = opts.to_dict()
        self.assertEqual(d['MACROS'], {'DEBUG': None, 'VER': 2})

    def test_to_dict_includes_other_fields(self):
        opts = (CompilerOpts(machine=['-mcpu=cortex-m4'])
            .define_flag('DEBUG'))
        d = opts.to_dict()
        self.assertIn('-mcpu=cortex-m4', d['MACHINE-OPTS'])
        self.assertIn('DEBUG', d['MACROS'])

    def test_define_overwrite_existing_key(self):
        opts = CompilerOpts().define_int('VER', 1).define_int('VER', 2)
        self.assertEqual(opts.macros['VER'], 2)
