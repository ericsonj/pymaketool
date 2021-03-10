import unittest

from pymakelib import prelib

class TestPrelib(unittest.TestCase):

    def test_add_to_list(self):
        list = []
        prelib.addToList(list, 'val1')
        self.assertIn('val1', list)
        prelib.addToList(list, {'key': ['val2']})
        self.assertIn('val2', list)
        prelib.addToList(list, {'key': 'val3'})
        self.assertIn('val3', list)
        prelib.addToList(list, {'key': ['val4', 'val5']})
        self.assertIn('val4', list)
        self.assertIn('val5', list)
        self.assertNotIn('key', list)
    

if __name__ == '__main__':
    unittest.main()