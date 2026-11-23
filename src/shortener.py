"""In-memory URL shortener backed by the custom hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import ChainingHashTable, LinearProbingHashTable


_MISSING = object()


class Shortener:
    def __init__(self, table_type=ChainingHashTable):
        self._url_to_code = table_type()
        self._code_to_url = table_type()
        self._next_id = 0

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or url != url.strip() or any(
            character.isspace() or ord(character) < 32 or ord(character) == 127
            for character in url
        ):
            raise ValueError("url must not contain surrounding or internal whitespace")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url is malformed") from error
        if parsed.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("url must have an http(s) scheme and a valid host")

    def shorten(self, url: str) -> str:
        self._validate_url(url)
        existing_code = self._url_to_code.get(url, _MISSING)
        if existing_code is not _MISSING:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code: str) -> str:
        if not isinstance(code, str):
            raise TypeError("code must be a string")
        url = self._code_to_url.get(code, _MISSING)
        if url is _MISSING:
            raise KeyError(code)
        return url


__all__ = ["Shortener", "ChainingHashTable", "LinearProbingHashTable"]
