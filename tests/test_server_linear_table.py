import http.client
import threading
import unittest
from http.server import HTTPServer

from src.hash_table import LinearProbingHashTable
from src.server import make_handler
from src.shortener import Shortener


class LinearTablePageTests(unittest.TestCase):
    def test_table_page_shows_linear_probe_path(self):
        shortener = Shortener(table_type=LinearProbingHashTable)
        shortener.shorten("https://example.com/linear")
        server = HTTPServer(("127.0.0.1", 0), make_handler(shortener))
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        try:
            connection.request("GET", "/table")
            response = connection.getresponse()
            page = response.read()
            self.assertEqual(response.status, 200)
            self.assertIn(b"Horner trace", page)
            self.assertIn(b"probe path", page)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join()

    def test_linear_table_shows_short_link_and_expandable_hash_steps(self):
        shortener = Shortener(table_type=LinearProbingHashTable)
        shortener.shorten("https://example.com/linear-details")
        server = HTTPServer(("127.0.0.1", 0), make_handler(shortener))
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        try:
            connection.request("GET", "/table")
            response = connection.getresponse()
            page = response.read()

            self.assertEqual(response.status, 200)
            self.assertIn(b"https://example.com/linear-details", page)
            self.assertIn(b'href="/s/0"', page)
            self.assertIn(b"<details>", page)
            self.assertIn(b"probe path", page)
            self.assertIn(b"31 *", page)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
