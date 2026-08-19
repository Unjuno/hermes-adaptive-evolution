import unittest

from counter import advance


class CounterFixtureTests(unittest.TestCase):
    def test_single_step(self):
        self.assertEqual(advance(4), 5)

    def test_multiple_steps(self):
        self.assertEqual(advance(4, 3), 7)

    def test_negative_value_is_rejected(self):
        with self.assertRaises(ValueError):
            advance(-1)

    def test_negative_steps_are_rejected(self):
        with self.assertRaises(ValueError):
            advance(1, -1)


if __name__ == "__main__":
    unittest.main()
