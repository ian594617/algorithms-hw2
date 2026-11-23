import unittest

from src.hash_table import LinearProbingHashTable
from src.shortener import Shortener


class LinearTableShortenerTests(unittest.TestCase):
    def test_shortener_works_with_linear_probing(self):
        shortener = Shortener(table_type=LinearProbingHashTable)
        first_url = "https://example.com/first"
        second_url = "https://example.com/second"

        first_code = shortener.shorten(first_url)
        second_code = shortener.shorten(second_url)
        self.assertEqual(first_code, "0")
        self.assertEqual(shortener.shorten(first_url), first_code)
        self.assertEqual(second_code, "1")
        self.assertEqual(shortener.expand(first_code), first_url)
        self.assertEqual(shortener.expand(second_code), second_url)


if __name__ == "__main__":
    unittest.main()
