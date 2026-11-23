"""Standard-library HTTP service for the URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, quote, unquote, urlsplit

from src.hash_table import ChainingHashTable, LinearProbingHashTable
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

        def _render_table_entry(self, entry, capacity: int) -> str:
            code = str(entry.value)
            short_link = "/s/" + quote(code, safe="")
            steps = []
            previous = 0
            for step, (character, value) in enumerate(
                zip(entry.key, entry.hash_trace), start=1
            ):
                steps.append(
                    "<li>"
                    + escape(
                        f"h_{step} = (31 * {previous} + ord({character!r})) "
                        f"% {capacity} = {value}"
                    )
                    + "</li>"
                )
                previous = value
            chain_position = (
                ""
                if entry.chain_position is None
                else f"; chain position: {entry.chain_position}"
            )
            details = (
                "<details><summary>Horner calculation</summary>"
                f"<p>Horner trace: {escape(str(entry.hash_trace))}</p>"
                f"<p>Start slot: {entry.hash_index}; probe path: "
                f"{escape(str(entry.probe_path))}{chain_position}</p>"
                f"<ol>{''.join(steps)}</ol></details>"
            )
            return (
                '<div class="node">'
                f"<p>URL: <code>{escape(entry.key)}</code></p>"
                f"<p>Code: <code>{escape(code)}</code></p>"
                f'<p>Short link: <a href="{escape(short_link)}">'
                f"{escape(short_link)}</a></p>{details}</div>"
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
                    "<th>URL, code, short link and hash details</th>"
                    "</tr></thead><tbody>",
                ]
                for (index, details), (_, entries) in zip(
                    table.debug_slots(), table.debug_slot_entries()
                ):
                    if entries:
                        content = ' <span class="chain-arrow">&rarr;</span> '.join(
                            self._render_table_entry(entry, table.capacity)
                            for entry in entries
                        )
                    else:
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


def serve(
    port: int = 8000,
    host: str = "",
    table_type: type[ChainingHashTable] | type[LinearProbingHashTable] = ChainingHashTable,
) -> None:
    shortener = Shortener(table_type=table_type)
    server = HTTPServer((host, port), make_handler(shortener))
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
    parser.add_argument(
        "--table-type", choices=("chaining", "linear"), default="chaining"
    )
    args = parser.parse_args()
    table_type = (
        ChainingHashTable
        if args.table_type == "chaining"
        else LinearProbingHashTable
    )
    serve(port=args.port, table_type=table_type)


if __name__ == "__main__":
    main()
