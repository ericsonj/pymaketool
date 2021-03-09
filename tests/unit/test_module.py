import unittest

from pymakelib import Module


class TestModule(unittest.TestCase):

    def test_src_type(self):
        self.assertIn('.c', Module.SrcType.C)
        self.assertIn('.C', Module.SrcType.CPP)
        

    def test_inc_type(self):
        self.assertIn('.h', Module.IncType.C)
        self.assertIn('.hpp', Module.IncType.CPP)


    def test_basic_c_module(self):
        class ModTest(Module.BasicCModule):
            pass
        
        mod = ModTest('mod')
        self.assertEqual('mod', mod.path)
        self.assertIsInstance(mod.getSrcs(), list)
        self.assertIsInstance(mod.getIncs(), list)


    def test_abstract_module(self):
        class ModTest(Module.AbstractModule):

            def getSrcs(self) -> list:
                return [
                    'mod/src/main.c'
                ]
            
            def getIncs(self) -> list:
                return [
                    'mod/inc/main.h'
                ]

        mod = ModTest('mod')
        self.assertEqual('mod', mod.path)
        self.assertIsInstance(mod.getSrcs(), list)
        self.assertIsInstance(mod.getIncs(), list)


if __name__ == '__main__':
    unittest.main()