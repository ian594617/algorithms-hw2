import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_encodes_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_known_encodings(self):
        expected = {
            0: "0",
            61: "Z",
            62: "10",
            3843: "ZZ",
            3844: "100",
        }
        for value, code in expected.items():
            with self.subTest(value=value):
                self.assertEqual(encode(value), code)

    def test_round_trip_values(self):
        for value in (1, 61, 62, 3844, 2**128):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_rejects_negative_values(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_rejects_non_integer_values(self):
        with self.assertRaises(TypeError):
            encode(True)

    def test_rejects_empty_or_invalid_codes(self):
        for code in ("", "a!"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)

    def test_rejects_non_string_codes(self):
        with self.assertRaises(TypeError):
            decode(62)


if __name__ == "__main__":
    unittest.main()
