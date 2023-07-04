# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest

class TestRain(unittest.TestCase):

    def test_dummy(self):
        self.assertEqual(1557, 1557)


if __name__ == '__main__':
    unittest.main()
