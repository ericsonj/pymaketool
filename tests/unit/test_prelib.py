import unittest

from pymakelib import prelib

class TestPrelib(unittest.TestCase):

    def test_add_to_list(self):
        list = []
        prelib.addToList(list, 'val1')
        self.assertIn('val2', list)