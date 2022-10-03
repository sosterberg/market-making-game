import unittest
import server


class MyTestCase(unittest.TestCase):
    def test_parse_correct_quote(self):
        bid_volume, bid, ask, ask_volume = server.parse_quote("10@20|30@40")
        self.assertEqual(bid_volume, 10)
        self.assertEqual(bid, 20)
        self.assertEqual(ask, 30)
        self.assertEqual(ask_volume, 40)


if __name__ == '__main__':
    unittest.main()
