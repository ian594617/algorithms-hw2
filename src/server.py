"""Standard-library HTTP service for the URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, quote, unquote, urlsplit

from src.shortener import Shortener


_MAX_FORM_BYTES = 1_000_000


def make_handler(shortener: Shortener):
    class ShortenerRequestHandler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, content: str, headers=()) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            for name, value in headers:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _page(self, title: str, body: str) -> str:
            return (
                "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
                f"<title>{escape(title)}</title><h1>{escape(title)}</h1>{body}</html>"
            )

        def _request_path(self):
            try:
                return urlsplit(self.path).path
            except ValueError:
                self._send_html(400, self._page("Bad Request", "<p>잘못된 경로입니다.</p>"))
                return None

        def do_GET(self):
            path = self._request_path()
            if path is None:
                return
            if path == "/":
                body = (
                    '<form action="/shorten" method="post">'
                    '<label>URL <input name="url" type="url" required></label>'
                    '<button type="submit">Shorten</button></form>'
                )
                self._send_html(200, self._page("URL Shortener", body))
                return
            if path == "/table":
                table = shortener.storage_table
                rows = [
                    "<p>Capacity: "
                    f"{table.capacity}; load factor: {table.load_factor:.3f}</p>",
                    "<table><thead><tr><th>Bucket/slot</th>"
                    "<th>Contents and hash/probe details</th></tr></thead><tbody>",
                ]
                for index, details in table.debug_slots():
                    content = "<br>".join(escape(detail) for detail in details)
                    rows.append(f"<tr><td>{index}</td><td>{content}</td></tr>")
                rows.append("</tbody></table>")
                self._send_html(200, self._page("Hash table", "".join(rows)))
                return
            if path.startswith("/s/"):
                code = unquote(path[len("/s/") :])
                try:
                    url = shortener.expand(code)
                except KeyError:
                    self._send_html(404, self._page("Not Found", "<p>코드가 없습니다.</p>"))
                    return
                location = quote(url, safe=":/?&=#%[]@!$&'()*+,;")
                self._send_html(
                    302,
                    self._page("Redirect", "<p>이동합니다.</p>"),
                    headers=(("Location", location),),
                )
                return
            self._send_html(404, self._page("Not Found", "<p>경로가 없습니다.</p>"))

        def do_POST(self):
            path = self._request_path()
            if path is None:
                return
            if path != "/shorten":
                self._send_html(404, self._page("Not Found", "<p>경로가 없습니다.</p>"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                content_length = -1
            if content_length < 0 or content_length > _MAX_FORM_BYTES:
                self._send_html(400, self._page("Bad Request", "<p>잘못된 폼 입력입니다.</p>"))
                return
            try:
                form_body = self.rfile.read(content_length).decode("utf-8")
                fields = parse_qsl(form_body, keep_blank_values=True, strict_parsing=True)
            except (UnicodeDecodeError, ValueError):
                self._send_html(400, self._page("Bad Request", "<p>잘못된 폼 입력입니다.</p>"))
                return
            urls = [value for name, value in fields if name == "url"]
            if len(urls) != 1:
                self._send_html(400, self._page("Bad Request", "<p>URL을 하나 입력하세요.</p>"))
                return
            try:
                code = shortener.shorten(urls[0])
            except (TypeError, ValueError) as error:
                self._send_html(400, self._page("Bad Request", f"<p>{escape(str(error))}</p>"))
                return

            link = escape("/s/" + quote(code, safe=""))
            result = (
                f'<p>짧은 코드: <a href="{link}">{escape(code)}</a></p>'
                f"<p>원본 URL: {escape(urls[0])}</p>"
            )
            self._send_html(200, self._page("Short URL created", result))

    return ShortenerRequestHandler


def serve(port: int = 8000, host: str = "") -> None:
    server = HTTPServer((host, port), make_handler(Shortener()))
    try:
        print(f"Serving on http://{host or '0.0.0.0'}:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener service")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(port=args.port)


if __name__ == "__main__":
    main()
