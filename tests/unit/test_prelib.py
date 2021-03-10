import unittest

from pymakelib import prelib
from pathlib import Path

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