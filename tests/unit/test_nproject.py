import unittest

from pymakelib import nproject


class TestNproject(unittest.TestCase):


    def test_basic_generator(self):

        class Test(nproject.BasicGenerator):

            def info(self) -> dict:
                return super().info()

            def get_attrs(self, **kwargs) -> dict:
                return {}

        t = Test()
        args = t.parse_args(["name=Ericson Joseph", "help"])
        self.assertDictEqual(args, {
            "name": "Ericson Joseph",
            "help": None
        })


if __name__ == '__main__':
    unittest.main()