import unittest
from pymakelib.generator import macrosDictToString
from pymakelib import Define as D


class TestMacrosDictToString(unittest.TestCase):

    def test_string_value_no_spaces(self):
        result = macrosDictToString({'VERSION': '1.0'})
        self.assertEqual(result, '-DVERSION=\\"1.0\\"')

    def test_string_value_with_spaces(self):
        result = macrosDictToString({'APP_NAME': 'My App'})
        self.assertEqual(result, "-DAPP_NAME='\\\"My App\\\"'")

    def test_bare_define_none(self):
        result = macrosDictToString({'DEBUG': None})
        self.assertEqual(result, '-DDEBUG')

    def test_bare_define_empty_string(self):
        result = macrosDictToString({'FLAG': ''})
        self.assertEqual(result, '-DFLAG')

    def test_bool_true(self):
        result = macrosDictToString({'ENABLE': True})
        self.assertEqual(result, '-DENABLE=1')

    def test_bool_false(self):
        result = macrosDictToString({'ENABLE': False})
        self.assertEqual(result, '-DENABLE=0')

    def test_define_object_no_spaces(self):
        result = macrosDictToString({'HEADER': D('config.h')})
        self.assertEqual(result, '-DHEADER=config.h')

    def test_define_object_with_spaces(self):
        result = macrosDictToString({'HEADER': D('my config.h')})
        self.assertEqual(result, "-DHEADER='my config.h'")

    def test_integer_value(self):
        result = macrosDictToString({'LEVEL': 3})
        self.assertEqual(result, '-DLEVEL=3')

    def test_multiple_macros_space_and_bare(self):
        result = macrosDictToString({'A': 'hello world', 'B': None})
        self.assertIn("-DA='\\\"hello world\\\"'", result)
        self.assertIn('-DB', result)

    def test_empty_dict(self):
        self.assertEqual(macrosDictToString({}), '')

    def test_non_dict_returns_empty(self):
        self.assertEqual(macrosDictToString(None), '')
        self.assertEqual(macrosDictToString([]), '')


class TestMacrosDictToStringValidation(unittest.TestCase):

    def test_key_starts_with_digit_raises(self):
        with self.assertRaises(ValueError):
            macrosDictToString({'2VERSION': '1.0'})

    def test_key_with_dash_raises(self):
        with self.assertRaises(ValueError):
            macrosDictToString({'MY-MACRO': None})

    def test_key_with_space_raises(self):
        with self.assertRaises(ValueError):
            macrosDictToString({'MY MACRO': None})

    def test_list_value_raises(self):
        with self.assertRaises(TypeError):
            macrosDictToString({'FLAGS': [1, 2, 3]})

    def test_dict_value_raises(self):
        with self.assertRaises(TypeError):
            macrosDictToString({'OPTS': {'a': 1}})

    def test_float_value_raises(self):
        with self.assertRaises(TypeError):
            macrosDictToString({'RATIO': 3.14})

    def test_valid_underscore_key_passes(self):
        result = macrosDictToString({'_MY_MACRO': None})
        self.assertEqual(result, '-D_MY_MACRO')
