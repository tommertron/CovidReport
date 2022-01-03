#!/usr/bin/env python3

import unittest

from datasources import ontgov


class TestOntarioDataSource(unittest.TestCase):
    def test_call(self):
        with self.assertRaises(NotImplementedError):
            ontgov.query()


if __name__ == "__main__":
    unittest.main()
