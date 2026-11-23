import http.client
import threading
import unittest
from http.server import HTTPServer
from urllib.parse import urlencode

from src.server import make_handler
from src.shortener import Shortener


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener()
        self.server = HTTPServer(
            ("127.0.0.1", 0), make_handler(self.shortener)
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_home_page_contains_url_form(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()

        self.assertEqual(response.status, 200)
        self.assertIn(b'<form', response.read())

    def test_post_shorten_returns_result_page(self):
        body = urlencode({"url": "https://example.com/path"})
        self.connection.request(
            "POST",
            "/shorten",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()

        self.assertEqual(response.status, 200)
        page = response.read()
        self.assertIn(b"/s/0", page)
        self.assertIn(b"https://example.com/path", page)

    def test_invalid_form_input_returns_400(self):
        body = urlencode({"url": "not-a-url"})
        self.connection.request(
            "POST",
            "/shorten",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()

        self.assertEqual(response.status, 400)
        response.read()

    def test_short_code_redirects_and_unknown_code_returns_404(self):
        self.shortener.shorten("https://example.com/redirect")
        self.connection.request("GET", "/s/0")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "https://example.com/redirect")
        response.read()

        self.connection.request("GET", "/s/missing")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 404)
        response.read()

    def test_table_page_shows_hash_and_probe_details(self):
        self.shortener.shorten("https://example.com/table")
        self.connection.request("GET", "/table")
        response = self.connection.getresponse()

        self.assertEqual(response.status, 200)
        page = response.read()
        self.assertIn(b"Horner trace", page)
        self.assertIn(b"chain position", page)

    def test_table_page_shows_linked_nodes_and_expandable_hash_steps(self):
        self.shortener.shorten("https://example.com/a")
        self.shortener.shorten("https://example.com/i")
        self.connection.request("GET", "/table")
        response = self.connection.getresponse()

        self.assertEqual(response.status, 200)
        page = response.read()
        for expected in (
            b"https://example.com/a",
            b"https://example.com/i",
            b"Short link:",
            b'href="/s/0"',
            b'href="/s/1"',
            b"&rarr;",
            b"<details>",
            b"<summary>",
            b"31 *",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)


if __name__ == "__main__":
    unittest.main()
