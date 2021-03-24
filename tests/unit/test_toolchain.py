import unittest

from pymakelib import toolchain

class TestToolchain(unittest.TestCase):

    def test_confgcc(self):
        res = toolchain.confGCC(binLocation="/usr/bin/")
        self.assertEqual("/usr/bin/gcc", res['CC'])
        res = toolchain.confGCC(binLocation="/usr/bin")
        self.assertEqual("/usr/bin/gcc", res['CC'])


if __name__ == '__main__':
    unittest.main()