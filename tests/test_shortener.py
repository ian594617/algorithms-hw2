import unittest

from src.hash_table import ChainingHashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener(table_type=ChainingHashTable)

    def test_shortens_and_expands_urls_with_sequential_base62_codes(self):
        first = self.shortener.shorten("https://example.com/one")
        second = self.shortener.shorten("https://example.com/two")

        self.assertEqual(first, "0")
        self.assertEqual(second, "1")
        self.assertEqual(self.shortener.expand(first), "https://example.com/one")
        self.assertEqual(self.shortener.expand(second), "https://example.com/two")

    def test_duplicate_url_reuses_code_without_consuming_an_id(self):
        url = "https://example.com/repeated"
        first = self.shortener.shorten(url)

        self.assertEqual(self.shortener.shorten(url), first)
        self.assertEqual(self.shortener.shorten("https://example.com/next"), "1")

    def test_invalid_urls_raise_value_error(self):
        invalid_urls = (
            "",
            "ftp://example.com/path",
            "http:///path",
            " https://example.com",
            "https://example.com ",
            "https://exa mple.com",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_invalid_argument_types_raise_type_error(self):
        with self.assertRaises(TypeError):
            self.shortener.shorten(123)
        with self.assertRaises(TypeError):
            self.shortener.expand(123)

    def test_unknown_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.shortener.expand("unknown")


if __name__ == "__main__":
    unittest.main()
